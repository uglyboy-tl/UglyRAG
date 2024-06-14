import json
from dataclasses import dataclass, field
from typing import Dict, List

from loguru import logger

from uglyrag.retriever import Retriever


@dataclass
class RetrieverEvaluation:
    test_dataset_path: str = "examples/retriever/qa.json"
    output_dir: str = "data/retriever_evaluation"
    dataset: Dict[str, List[str]] = field(init=False, default_factory=dict)
    index_data: Dict[str, str] = field(init=False, default_factory=dict)

    def __post_init__(self):
        with open(self.test_dataset_path, "r") as f:
            data = json.loads(f.read())

        queries: Dict[str, str] = data["queries"]
        relevant_docs: Dict[str, List[str]] = data["relevant_docs"]

        for id, query in queries.items():
            self.dataset[query] = relevant_docs[id]
        self.index_data = data["corpus"]

    def get_index_data(self) -> List[str]:
        return self.index_data.values()

    def evaluate(self, retriever: Retriever):
        sum_recall: int = 0
        sum_score: float = 0
        for query, ids in self.dataset.items():
            result_list = retriever.search(query)
            answer = self.index_data[ids[0]]
            if answer in result_list:
                sum_recall += 1
                index = result_list.index(answer) + 1
                sum_score += 1.0 / index

        logger.info(f"recall: {sum_recall / len(self.dataset)}")
        logger.info(f"mrr: {sum_score / len(self.dataset)}")
