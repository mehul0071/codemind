from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import settings
from app.db.base import Base

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine, 
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    pass 