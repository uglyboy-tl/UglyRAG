from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, default="")
    path: Mapped[Optional[str]] = mapped_column(String, default="")
    content: Mapped[str] = mapped_column(Text)
    indexed_cols = ["title", "content"]

    @classmethod
    def get_instance(cls, doc: str) -> "Document":
        return cls(title="", path="", content=doc)
