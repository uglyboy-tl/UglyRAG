import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


@dataclass
class Item:
    id: int
    question: str
    golden_answers: List[str]
    medadata: dict = field(default_factory=dict)
    output: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load_json(cls, json_str: str) -> Optional["Item"]:
        try:
            item_dict = json.loads(json_str)
        except Exception as e:
            logger.error(f"Loading '{json_str}' with ERROR : {e}")
            return None
        id = item_dict.get("id")
        question = item_dict.get("question")
        golden_answers = item_dict.get("golden_answers")
        metadata = item_dict.get("metadata", {})
        output = item_dict.get("output", {})
        return cls(id, question, golden_answers, metadata, output)

    def update_output(self, key: str, value: Any):
        if key in ["id", "question", "golden_answers", "output"]:
            raise AttributeError(f"{key} should not be changed")
        else:
            self.output[key] = value

    def update_evaluation_score(self, metric_name, metric_score):
        r"""Update the evaluation score of this sample for a metric."""
        if "metric_score" not in self.output:
            self.output["metric_score"] = {}
        self.output["metric_score"][metric_name] = metric_score

    def to_dict(self):
        output = {
            "id": self.id,
            "question": self.question,
            "golden_answers": self.golden_answers,
            "output": self.output,
        }
        if self.metadata != {}:
            output["metadata"] = self.metadata

        return output

    def __getattr__(self, attr_name):
        if attr_name in ["id", "question", "golden_answers", "metadata", "output"]:
            return super().__getattribute__(attr_name)
        else:
            output = super().__getattribute__("output")
            if attr_name in output:
                return output[attr_name]
            else:
                raise AttributeError(f"Attribute `{attr_name}` not found")


@dataclass
class Dataset:
    dataset_name: str
    dataset_path: str
    sample_num: Optional[int] = field(default=None)
    random_sample: bool = False
    _dataset_path: Path = field(init=False)
    _data: List[Item] = field(default_factory=list)

    def __post_init__(self):
        self._dataset_path = Path(self.dataset_path)
        if not self.data:
            self.data = self._load_data(self.dataset_name, self.dataset_path)

    def _load_data(self):
        """Load data from the provided dataset_path or directly download the file(TODO)."""

        if not self._dataset_path.exists():
            # TODO: auto download: self._download(dataset_name, dataset_path)
            pass

        data = []
        with self._dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                item = Item.load_json(line)
                data.append(item)
        if self.sample_num is not None:
            if self.random_sample:
                logger.info(f"Random sample {self.sample_num} items in test set.")
                data = random.sample(data, self.sample_num)
            else:
                data = data[: self.sample_num]

        return data

    def update_output(self, key: str, value_list: List[Any]):
        assert len(self.data) == len(value_list)
        for item, value in zip(self.data, value_list, strict=False):
            item.update_output(key, value)

    @property
    def question(self):
        return [item.question for item in self.data]

    @property
    def golden_answers(self):
        return [item.golden_answers for item in self.data]

    @property
    def id(self):
        return [item.id for item in self.data]

    @property
    def output(self):
        return [item.output for item in self.data]

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)

    @property
    def data(self):
        return self._data

    def save(self, save_path):
        """Save the dataset into the original format."""

        save_data = [item.to_dict() for item in self.data]
        with open(save_path, "w") as f:
            json.dump(save_data, f, indent=4)
