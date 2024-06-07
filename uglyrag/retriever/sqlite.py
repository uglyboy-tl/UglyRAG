from dataclasses import dataclass
from typing import Generic, List, Type, TypeVar

from loguru import logger
from sqlalchemy import Integer, Text, event, schema, select, text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm.session import Session

from .base import Retriever
from .database import Base, BaseDB, Document
from .tokenizer import get_tokenizer

T = TypeVar("T", bound=Base)


@compiles(schema.CreateTable, "sqlite")
def _compile(element: schema.CreateTable, compiler, **kw):
    if not element.target.info.get("use_fts5", False):
        return compiler.visit_create_table(element, **kw)
    name = compiler.preparer.format_table(element.target)
    cols = [compiler.preparer.format_column(col) for col in element.target.columns]
    cols = ", ".join([col for col in cols if col != "rowid"])
    return f"CREATE VIRTUAL TABLE {name} USING fts5({cols})"


class DataIndex(Base):
    __tablename__ = "index_data_fts"
    __table_args__ = {"info": {"use_fts5": True}}
    rowid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_index: Mapped[str] = mapped_column(Text)


@dataclass
class SQLite(BaseDB, Retriever, Generic[T]):
    db_url: str = "sqlite:///data/sqlite.db"
    dataType: Type[T] = Document

    # 类变量
    # BaseTokenizer 类型的分词器
    tokenizer = get_tokenizer()

    @classmethod
    def transform_data(cls, data: T):
        data_segment = []
        for col in data.indexed_cols:
            if not hasattr(data, col):
                continue
            body = getattr(data, col)
            data_segment.extend(cls.tokenizer(body))
        data_index = " ".join(data_segment)
        return data_index

    def _create_table(self, Table: T) -> None:
        super()._create_table(DataIndex)
        super()._create_table(Table)

    def index(self, docs: List[str]):
        logger.info("正在构建索引(SQLite FTS5)...")
        for doc in docs:
            self.add(self.dataType.get_instance(doc))
        logger.success("索引构建完成")

    def search(self, query: str) -> List[str]:
        query_list = self.tokenizer(query)
        logger.debug(f"搜索关键词: {query_list}")
        with self.Session() as db:
            stmt = (
                select(self.dataType)
                .select_from(self.dataType)
                .join(DataIndex, self.dataType.id == DataIndex.rowid)
                .where(DataIndex.data_index.match(f"{' OR '.join(query_list)}"))
                # .order_by(text(f"bm25({DataIndex.__tablename__})"))
                .limit(self.topk)
            )
            results = db.scalars(stmt).all()
            return [str(result.content) for result in results]


@event.listens_for(Session, "before_flush")
def before_flush(session, flush_context, instances):
    for instance in session.new:
        if isinstance(instance, Base):
            data_index = SQLite.transform_data(instance)
            autoinsert = DataIndex(data_index=data_index)
            session.add(autoinsert)
