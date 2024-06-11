from dataclasses import dataclass, field
from typing import List

from uglyrag.generator import BasePromptTemplate, Generator, OpenAI_Generator

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
class AbstractiveRecompRefiner(Refiner):
    generator: Generator = field(init=False)

    def __post_init__(self) -> None:
        self.generator = OpenAI_Generator(prompt_template=BasePromptTemplate(PROMPT_TEMPLATE))

    def __call__(self, query: str, contexts: List[str]) -> List[str]:
        return [self.generator(query, contexts)]