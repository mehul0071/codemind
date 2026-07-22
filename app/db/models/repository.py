from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class RepositoryStatus(str, PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    repo_url = Column(String(1000), nullable=True)
    local_path = Column(String(1000), nullable=True)
    status = Column(Enum(RepositoryStatus, name="repository_status"), 
            nullable=False, default=RepositoryStatus.PENDING, server_default=RepositoryStatus.PENDING.value)
    metadata_info = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="repositories")

    def __repr__(self):
        return (
            f"<Repository(id={self.id}, "
            f"session_id='{self.session_id}', "
            f"status='{self.status}')>"
        )