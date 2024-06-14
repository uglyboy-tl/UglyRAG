import json
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

from eval.dataset import Dataset
from eval.evaluator import Evaluator
from uglyrag import Pipeline


@dataclass
class RAGEvaluation:
    index_path: str = "examples/indexes/sample_data.jsonl"
    test_dataset_path: str = "examples/dataset/test.jsonl"
    output_dir: str = "data/rag_evaluation"
    dataset: Dataset = field(init=False)
    evaluator: Evaluator = field(init=False)

    def __post_init__(self):
        self.dataset = Dataset(dataset_name="test", dataset_path=self.test_dataset_path)
        self.evaluator = Evaluator(self.output_dir)

    def get_index_data(self):
        index_data = []
        with open(self.index_path, "r") as f:
            while True:
                new_line = f.readline()
                if not new_line:
                    break
                new_item = json.loads(new_line)
                index_data.append(new_item)
        return index_data

    def evaluate(self, rag: Pipeline):
        pred_answer_list = [rag.process(question) for question in self.dataset.question]
        self.dataset.update_output("pred", pred_answer_list)
        self.dataset.save(Path(self.output_dir) / "eval_details.jsonl")
        eval_result = self.evaluator.evaluate(self.dataset)
        logger.success(eval_result)
