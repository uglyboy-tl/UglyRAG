from uglyrag import Pipeline
from uglyrag.retriever.sqlite import SQLite

retriever = SQLite(init_needed=True)
retriever.index(["我爱北京天安门", "天安门上太阳升", "伟大领袖毛主席", "指引我们向前进"])
rag = Pipeline(retriever)
rag.process("天安门在哪里？")
