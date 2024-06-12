from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    indexed_content: Mapped[str] = mapped_column(Text)
    original_content: Mapped[str] = mapped_column(Text)
    indexed_cols = ["indexed_content"]

    @classmethod
    def get_instance(cls, index: str, content: str) -> "Document":
        return cls(indexed_content=index, original_content=content)
