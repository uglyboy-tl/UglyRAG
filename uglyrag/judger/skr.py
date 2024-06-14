from dataclasses import dataclass

from .base import Judger


@dataclass
class SKRJudger(Judger):
    _name_ = "SKR"
    """Implementation for SKR-knn
    Paper link: https://aclanthology.org/2023.findings-emnlp.691.pdf
    """

    pass
