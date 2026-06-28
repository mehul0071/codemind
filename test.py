# import asyncio
# from sqlalchemy.ext.asyncio import create_async_engine
# from app.config import settings

# async def test_connection():
#     engine = create_async_engine(settings.DATABASE_URL, echo=True)
#     try:
#         async with engine.connect() as conn:
#             result = await conn.execute("SELECT 1")
#             print("Database connection successful!")
#     except Exception as e:
#         print("Error:", e)
#     finally:
#         await engine.dispose()

# asyncio.run(test_connection())

# from app.parsers.python_parser import PythonParser

# parser = PythonParser()
# elements = parser.parse_directory("path/to/your/test/repo")

# print(f"Total elements extracted: {len(elements)}")
# for el in elements[:5]:   # print first 5
#     print(f"{el['type']}: {el['name']} in {el['file_path']}")

# from app.rag.chunker import CodeChunker

# chunker = CodeChunker()

# documents = chunker.parse_and_chunk_directory("path/to/your/python/project")

# print(f"Total chunks created: {len(documents)}")

# # Check one document
# print(documents[0].page_content[:300])
# print(documents[0].metadata)