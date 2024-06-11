from eval import Evaluation
from uglyrag import Pipeline
from uglyrag.retriever.sqlite import SQLite

eval = Evaluation("examples/indexes/sample_data.jsonl", "examples/dataset/test.jsonl")
retriever = SQLite(init_needed=True)
retriever.index([item.get("contents") for item in eval.get_index_data()])
# retriever = SQLite()
rag = Pipeline(retriever)
eval.evaluate(rag)
