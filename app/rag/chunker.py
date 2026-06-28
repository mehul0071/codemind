from typing import List, Dict
from langchain_core.documents import Document
from app.parsers.python_parser import PythonParser


class CodeChunker:

    def __init__(self, max_chunk_size: int = 800):
        self.parser = PythonParser()
        self.max_chunk_size = max_chunk_size
    
    def create_chunks(self, parsed_elements: List[Dict]) -> List[Document]:
        documents = []
        
        for element in parsed_elements:
            doc = self._create_main_chunk(element)
            documents.append(doc)
            
            if element.get("type") in ["class", "module"] and len(element.get("code_snippet", "")) > 600:
                summary_doc = self._create_summary_chunk(element)
                if summary_doc:
                    documents.append(summary_doc)
        
        return documents
    
    def _create_main_chunk(self, element: Dict) -> Document:
        content = self._build_content(element)
        
        metadata = {
            "name": element.get("name"),
            "type": element.get("type"),
            "file_path": element.get("file_path"),
            "line_start": element.get("line_start"),
            "line_end": element.get("line_end"),
            "language": "python",
            "is_class": element.get("type") == "class",
            "is_function": element.get("type") in ["function", "async_function"],
            "has_docstring": bool(element.get("docstring")),
            "chunk_type": "main"
        }
        
        if element.get("metadata"):
            metadata.update(element["metadata"])
        
        return Document(page_content=content, metadata=metadata)
    
    def _create_summary_chunk(self, element: Dict) -> Document | None:
        docstring = element.get("docstring", "")
        if not docstring:
            return None
            
        content = f"Summary of {element.get('type')} {element.get('name')}:\n{docstring}"
        
        metadata = {
            "name": element.get("name"),
            "type": element.get("type"),
            "file_path": element.get("file_path"),
            "chunk_type": "summary",
            "is_summary": True
        }
        
        return Document(page_content=content, metadata=metadata)
    
    def _build_content(self, element: Dict) -> str:
        name = element.get("name", "")
        chunk_type = element.get("type", "").capitalize()
        docstring = element.get("docstring", "").strip()
        code = element.get("code_snippet", "").strip()
        parts = [f"{chunk_type}: {name}"]
        
        if docstring:
            parts.append(f"Docstring:\n{docstring}")
        
        if code:
            parts.append(f"Code:\n{code}")
        
        return "\n\n".join(parts)