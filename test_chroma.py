from app.vectorstore.chroma import ChromaVectorStore

store = ChromaVectorStore()
collection = store.client.get_collection("codemind_codebase")

print("Total documents:", collection.count())

docs = collection.get(include=["metadatas"])
print("Metadata sample:", docs['metadatas'][:2] if docs['metadatas'] else "No documents")