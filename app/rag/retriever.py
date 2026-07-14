import os
import networkx as nx
from typing import List, Tuple, Optional, Set
from langchain_core.documents import Document
from app.rag.embeddings import embeddings
from app.config import settings
from app.db.sessions import AsyncSessionLocal
from app.db.models.document_chunk import DocumentChunk
from app.db.models.code_relation import CodeRelation
from app.db.models.repository import Repository
from sqlalchemy import select, or_, and_


class CodeRetriever:
    def __init__(self):
        self.embeddings = embeddings

    async def _get_repo_path(self, session_id: str) -> str:
        async with AsyncSessionLocal() as db:
            stmt = select(Repository).where(Repository.session_id == session_id)
            result = await db.execute(stmt)
            repo = result.scalar_one_or_none()
            if repo:
                if repo.local_path and os.path.exists(repo.local_path):
                    return os.path.abspath(repo.local_path)
                repo_name = repo.metadata_info.get("repo_name")
                if repo_name:
                    possible_path = os.path.abspath(os.path.join(settings.DATA_PATH, session_id, repo_name))
                    if os.path.exists(possible_path):
                        return possible_path
                    if os.path.exists(os.path.join(os.getcwd(), repo_name)):
                        return os.path.abspath(os.path.join(os.getcwd(), repo_name))
        return os.getcwd()

    async def _build_relation_graph(self, session_id: str) -> nx.DiGraph:
        G = nx.DiGraph()
        async with AsyncSessionLocal() as db:
            stmt = select(CodeRelation).where(CodeRelation.session_id == session_id)
            result = await db.execute(stmt)
            relations = result.scalars().all()

        for rel in relations:
            G.add_edge(
                rel.source_name,
                rel.target_name,
                relation_type=rel.relation_type,
                source_type=rel.source_type,
                target_type=rel.target_type,
                metadata=rel.metadata_info
            )
        return G

    async def _expand_context(
        self,
        chunks: List[DocumentChunk],
        session_id: str,
        max_expanded: int = 4
    ) -> List[DocumentChunk]:
        if not chunks:
            return chunks

        repo_path = await self._get_repo_path(session_id)
        G = await self._build_relation_graph(session_id)

        if not G.nodes:
            return chunks

        classes_to_fetch: Set[str] = set()
        functions_to_fetch: Set[str] = set()
        files_to_fetch: Set[str] = set()
        specific_entities_to_fetch: Set[Tuple[str, str]] = set()

        for chunk in chunks:
            chunk_rel_path = None
            if chunk.file_path:
                try:
                    chunk_rel_path = os.path.relpath(chunk.file_path, repo_path)
                except Exception:
                    chunk_rel_path = chunk.file_path

            # 1. Class inheritance
            if chunk.type == "class" and chunk.name:
                if chunk.name in G:
                    # Parents (outgoing inherits edges)
                    parents = [
                        v for u, v, d in G.out_edges(chunk.name, data=True)
                        if d.get("relation_type") == "inherits"
                    ]
                    classes_to_fetch.update(parents)
                    # Subclasses (incoming inherits edges)
                    subclasses = [
                        u for u, v, d in G.in_edges(chunk.name, data=True)
                        if d.get("relation_type") == "inherits"
                    ]
                    classes_to_fetch.update(subclasses)

            # 2. Function/Method calls
            elif chunk.type in ["function", "async_function"] and chunk.name:
                matching_nodes = []
                for node in G.nodes:
                    if str(node) == chunk.name or str(node).endswith(f".{chunk.name}"):
                        matching_nodes.append(node)
                
                for node in matching_nodes:
                    # Called functions (outgoing calls edges)
                    called = [
                        v for u, v, d in G.out_edges(node, data=True)
                        if d.get("relation_type") == "calls"
                    ]
                    functions_to_fetch.update(called)
                    # Calling functions (incoming calls edges)
                    calling = [
                        u for u, v, d in G.in_edges(node, data=True)
                        if d.get("relation_type") == "calls"
                    ]
                    functions_to_fetch.update(calling)

            # 3. File imports & specific imported names
            if chunk_rel_path and chunk_rel_path in G:
                imports = [
                    (v, d) for u, v, d in G.out_edges(chunk_rel_path, data=True)
                    if d.get("relation_type") == "imports"
                ]
                for target_file, d in imports:
                    meta = d.get("metadata", {})
                    imported_name = meta.get("imported_name")
                    if imported_name and imported_name not in ["*", None]:
                        specific_entities_to_fetch.add((target_file, imported_name))
                    else:
                        files_to_fetch.add(target_file)

        # Build DB query conditions
        conditions = []
        if classes_to_fetch:
            conditions.append(and_(
                DocumentChunk.type == 'class',
                DocumentChunk.name.in_(list(classes_to_fetch))
            ))
        if functions_to_fetch:
            simple_func_names = set()
            for f in functions_to_fetch:
                if "." in str(f):
                    simple_func_names.add(str(f).split(".")[-1])
                else:
                    simple_func_names.add(str(f))
            if simple_func_names:
                conditions.append(and_(
                    DocumentChunk.type.in_(['function', 'async_function']),
                    DocumentChunk.name.in_(list(simple_func_names))
                ))
        
        abs_files_to_fetch = [
            os.path.abspath(os.path.join(repo_path, f))
            for f in files_to_fetch
        ]
        if abs_files_to_fetch:
            conditions.append(and_(
                DocumentChunk.type == 'module',
                DocumentChunk.file_path.in_(abs_files_to_fetch)
            ))

        for rel_file, name in specific_entities_to_fetch:
            abs_file = os.path.abspath(os.path.join(repo_path, rel_file))
            conditions.append(and_(
                DocumentChunk.file_path == abs_file,
                DocumentChunk.name == name
            ))

        expanded_chunks = []
        if conditions:
            stmt = select(DocumentChunk).where(
                and_(
                    DocumentChunk.session_id == session_id,
                    or_(*conditions)
                )
            )
            async with AsyncSessionLocal() as db:
                result = await db.execute(stmt)
                expanded_chunks = result.scalars().all()

        # Deduplicate expanded chunks against original chunks
        original_keys = {
            (c.file_path, c.name, c.type) for c in chunks
        }
        
        added_count = 0
        final_chunks = list(chunks)
        for ec in expanded_chunks:
            key = (ec.file_path, ec.name, ec.type)
            if key not in original_keys:
                final_chunks.append(ec)
                original_keys.add(key)
                added_count += 1
                if added_count >= max_expanded:
                    break

        return final_chunks

    async def retrieve(self, query: str, session_id: str, k: int = 8) -> List[Document]:
        try:
            query_embedding = self.embeddings.embed_query(query)
            async with AsyncSessionLocal() as db:
                stmt = (
                    select(DocumentChunk)
                    .where(DocumentChunk.session_id == session_id)
                    .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
                    .limit(k)
                )
                result = await db.execute(stmt)
                chunks = result.scalars().all()

            # Expand chunks via relational graph
            expanded_chunks = await self._expand_context(chunks, session_id)
                
            docs = []
            for chunk in expanded_chunks:
                docs.append(Document(
                    page_content=chunk.content,
                    metadata={
                        "name": chunk.name,
                        "type": chunk.type,
                        "file_path": chunk.file_path,
                        "session_id": chunk.session_id
                    }
                ))
            return docs
        except Exception as e:
            print(f"Error in retrieve: {e}")
            return []

    async def retrieve_with_scores(self, query: str, session_id: str, k: int = 8) -> List[Tuple[Document, float]]:
        try:
            query_embedding = self.embeddings.embed_query(query)
            distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding)
            async with AsyncSessionLocal() as db:
                stmt = (
                    select(DocumentChunk, distance_expr.label("distance"))
                    .where(DocumentChunk.session_id == session_id)
                    .order_by(distance_expr)
                    .limit(k)
                )
                result = await db.execute(stmt)
                rows = result.all()

            original_chunks = [row[0] for row in rows]
            chunk_to_score = {
                (c.file_path, c.name, c.type): float(score)
                for c, score in rows
            }

            expanded_chunks = await self._expand_context(original_chunks, session_id)
                
            docs_with_score = []
            for chunk in expanded_chunks:
                doc = Document(
                    page_content=chunk.content,
                    metadata={
                        "name": chunk.name,
                        "type": chunk.type,
                        "file_path": chunk.file_path,
                        "session_id": chunk.session_id
                    }
                )
                key = (chunk.file_path, chunk.name, chunk.type)
                score = chunk_to_score.get(key, 0.5)
                docs_with_score.append((doc, score))
            return docs_with_score
        except Exception as e:
            print(f"Error in retrieve_with_scores: {e}")
            return []

    async def get_relevant_documents(self, query: str, session_id: str, k: int = 8) -> List[Document]:
        return await self.retrieve(query, session_id, k)