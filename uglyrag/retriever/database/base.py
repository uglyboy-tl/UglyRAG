from dataclasses import dataclass, field
from typing import Dict, List, Type, TypeVar

from sqlalchemy import Engine, Integer, MetaData, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    indexed_content: Mapped[str] = mapped_column(Text)
    original_content: Mapped[str] = mapped_column(Text)
    indexed_cols = ["indexed_content"]


T = TypeVar("T", bound=Base)


@dataclass
class BaseDB:
    db_url: str = field(default="")
    init_needed: bool = False
    config: Dict[str, str] = field(default_factory=dict)
    engine: Engine = field(init=False)
    metadata: MetaData = field(default_factory=lambda: MetaData())
    Session: Type = field(init=False)
    all_tables: List[str] = field(default_factory=lambda: [])

    def __post_init__(self):
        self.db_url = self.config.get("db_url", self.db_url)
        self.engine = create_engine(self.db_url)
        # self.engine = create_engine(self.db_url, echo=True)  # debug
        self.metadata.reflect(self.engine)
        self.all_tables = list(self.metadata.tables.keys())
        if self.init_needed:
            self.metadata.drop_all(self.engine)
            self.all_tables = []
        self.Session = sessionmaker(bind=self.engine)

    def _has_table(self, table_name: str) -> bool:
        return table_name in self.all_tables

    def _create_table(self, Table: Type[Base]) -> None:
        if not self._has_table(Table.__tablename__):
            self.all_tables.append(Table.__tablename__)
            Table.metadata.create_all(self.engine)

    def add(self, data: T) -> None:
        with self.Session() as session:
            self._create_table(data.__class__)
            session.add(data)
            session.commit()
