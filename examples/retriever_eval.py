from eval import RetrieverEvaluation
from uglyrag.retriever import get_retriever_class

eval = RetrieverEvaluation()

# retriever = get_retriever_class("SQLite")(db_url="sqlite:///data/evaluator.db", init_needed=True)
# retriever = get_retriever_class("Chroma")(collection_name="evaluator", init_needed=True)
# retriever.index(eval.get_index_data())


retriever = get_retriever_class("SQLite")(db_url="sqlite:///data/evaluator.db")
# retriever = get_retriever_class("Chroma")(collection_name="evaluator")
# Evaluate
eval.evaluate(retriever)
