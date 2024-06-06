from abc import ABC
from dataclasses import dataclass, field
from typing import List, Type, TypeVar

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    indexed_cols = []


T = TypeVar("T", bound=Base)


@dataclass
class BaseDB(ABC):
    db_url: str
    init_needed: bool = False
    engine: Engine = field(init=False)
    metadata: MetaData = field(default_factory=lambda: MetaData())
    Session: Type = field(init=False)
    all_tables: List[str] = field(default_factory=lambda: [])

    def __post_init__(self):
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
