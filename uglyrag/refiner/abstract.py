from dataclasses import dataclass, field
from typing import List

from uglyrag.generator import Generator, get_generator_class

from .base import Refiner

PROMPT_TEMPLATE = """
Given the question and the document, summarize the document.
======
## Question:
{question}

## Document:
{reference}

## Summary:
"""


@dataclass
class AbstractRefiner(Refiner):
    """Implementation for Abstractive RECOMP compressor:
    RECOMP: Improving Retrieval-Augmented LMs with Compression and Selective Augmentation.
    """

    _name_ = "Abstract"
    generator: Generator = field(init=False)

    def __post_init__(self) -> None:
        self.generator = get_generator_class("OpenAI")(PROMPT_TEMPLATE)

    def __call__(self, query: str, contexts: List[str]) -> List[str]:
        return [self.generator(query, contexts)]
