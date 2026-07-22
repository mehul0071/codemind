import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    GROQ_API_KEY: str
    MODEL_NAME: str = "llama-3.3-70b-versatile"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DB_PATH: str = "vector_store"
    DATA_PATH: str = "data"
    DATABASE_URL: str = "postgresql+asyncpg://mehul:mehul0071@localhost:5432/codemind"
    WORKSPACE_PATH: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    API_KEY: str = ""
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "codemind"
    
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    class Config:
        env_file = ".env"

settings = Settings()

os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
if settings.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT