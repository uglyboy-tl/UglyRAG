from eval import RAGEvaluation
from uglyrag import Pipeline
from uglyrag.retriever import get_retriever_class

eval = RAGEvaluation()

# Build Index
# retriever = get_retriever_class("SQLite")(init_needed=True)
# retriever.index([item.get("contents") for item in eval.get_index_data()])
# retriever = get_retriever_class("Chroma")(init_needed=True)
# retriever.index([item.get("contents") for item in eval.get_index_data()])

# Pipeline Config
config = {
    "retriever": "Chroma",
    "judger": "LLM",
    "refiner": "Abstract",
}

rag = Pipeline(config=config)

# Evaluate
eval.evaluate(rag)
