from uglyrag import Pipeline
from uglyrag.retriever import get_retriever_class

query = "天安门在哪里？"
retriever = get_retriever_class("SQLite")(db_url="sqlite:///data/test_sqlite.db", init_needed=True)
# retriever = Chroma(collection_name="test", init_needed=True)
rag = Pipeline(retriever)
rag.process(query, ["我爱北京天安门", "天安门上太阳升", "伟大领袖毛主席", "指引我们向前进"])
