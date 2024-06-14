import json
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger


@dataclass
class RetrieverEvaluation:
    index_path: str = "examples/indexes/sample_data.jsonl"
    test_dataset_path: str = "examples/dataset/test.jsonl"
    output_dir: str = "data/evaluation"
