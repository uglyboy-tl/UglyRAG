# Source: https://github.com/RUC-NLPIR/FlashRAG/blob/main/flashrag/evaluator/evaluator.py
# Copyright (c) 2024 Jiajie Jin.
# MIT License

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set, Type, TypeVar

from ..dataset import Dataset
from .metrics import BaseMetric


@dataclass
class Evaluator:
    save_dir: str = "Evaluation"
    save_metric_flag: bool = False
    save_data_flag: bool = False
    metrics: List[str]
    avaliable_metrics: Dict[str, Type[BaseMetric]] = field(init=False)
    metric_class: Dict[str, Any] = field(default_factory=dict)
    _save_dir: Path = field(init=False)

    def __post_init__(self):
        self._save_dir = Path(self.save_dir)
        if not self._save_dir.exists():
            self._save_dir.mkdir(parents=True)

        self.avaliable_metrics = self._collect_metrics()

        for metric in self.metrics:
            if metric in self.avaliable_metrics:
                self.metric_class[metric] = self.avaliable_metrics[metric](self.config)
            else:
                print(f"{metric} has not been implemented!")
                raise NotImplementedError

    def _collect_metrics(self) -> Dict[str, Type[BaseMetric]]:
        """Collect all classes based on ```BaseMetric```."""
        T = TypeVar("T")

        def find_descendants(base_class: T, subclasses=None) -> Set[Type[T]]:
            if subclasses is None:
                subclasses = set()

            direct_subclasses = base_class.__subclasses__()
            for subclass in direct_subclasses:
                if subclass not in subclasses:
                    subclasses.add(subclass)
                    find_descendants(subclass, subclasses)
            return subclasses

        avaliable_metrics = {}
        for cls in find_descendants(BaseMetric):
            metric_name = cls.metric_name
            avaliable_metrics[metric_name] = cls
        return avaliable_metrics

    def evaluate(self, dataset: Dataset):
        """Calculate all metric indicators and summarize them."""

        result_dict = {}
        for metric in self.metrics:
            try:
                metric_result, metric_scores = self.metric_class[metric].calculate_metric(dataset)
                result_dict.update(metric_result)

                for metric_score, item in zip(metric_scores, dataset, strict=False):
                    item.update_evaluation_score(metric, metric_score)
            except Exception as e:
                print(f"Error in {metric}!")
                print(e)
                continue

        if self.save_metric_flag:
            self.save_metric_score(result_dict)

        if self.save_data_flag:
            self.save_data(dataset)

        return result_dict

    def save_metric_score(self, result_dict):
        file_name = "metric_score.txt"
        save_path = self._save_dir / file_name
        with open(save_path, "w", encoding="utf-8") as f:
            for k, v in result_dict.items():
                f.write(f"{k}: {v}\n")

    def save_data(self, dataset: Dataset):
        file_name = "intermediate_data.json"
        save_path = self._save_dir / file_name

        dataset.save(save_path)
