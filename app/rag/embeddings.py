from langchain_huggingface import HuggingFaceEmbeddings
from app.config import settings

embeddings = HuggingFaceEmbeddings(
    model_name=settings.EMBEDDING_MODEL
)
