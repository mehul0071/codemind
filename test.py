import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings

async def test_connection():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    try:
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            print("Database connection successful!")
    except Exception as e:
        print("❌ Error:", e)
    finally:
        await engine.dispose()

asyncio.run(test_connection())