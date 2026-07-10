from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from app.db.base import Base


class CodeRelation(Base):
    __tablename__ = "code_relations"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(
        Integer,
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(String(255), nullable=False, index=True)

    source_type = Column(String(50), nullable=False)
    source_name = Column(String(1000), nullable=False, index=True)

    target_type = Column(String(50), nullable=False)
    target_name = Column(String(1000), nullable=False, index=True)

    relation_type = Column(String(50), nullable=False, index=True)

    metadata_info = Column(JSON, nullable=False, default=dict)

    def __repr__(self):
        return (
            f"<CodeRelation(id={self.id}, "
            f"session_id='{self.session_id}', "
            f"relation='{self.source_name} --[{self.relation_type}]--> {self.target_name}')>"
        )
