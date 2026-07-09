from sqlalchemy import Column, Integer, String, Text, ForeignKey
from pgvector.sqlalchemy import Vector
from app.db.base import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(
        Integer,
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(String(255), nullable=False, index=True)
    file_path = Column(String(1000), nullable=False)
    name = Column(String(255), nullable=True)
    type = Column(String(50), nullable=True)  # module, class, function, async_function
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=False)  # 384 dimensions for all-MiniLM-L6-v2

    def __repr__(self):
        return (
            f"<DocumentChunk(id={self.id}, "
            f"session_id='{self.session_id}', "
            f"file_path='{self.file_path}', "
            f"type='{self.type}')>"
        )
