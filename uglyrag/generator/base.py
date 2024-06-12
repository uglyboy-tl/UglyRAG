from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

from .prompt import PromptTemplate


@dataclass
class Generator(ABC):
    @abstractmethod
    def __call__(self, query: str, retrieval_results: Optional[List[str]] = None) -> str:
        pass


@dataclass
class LLM(Generator):
    prompt: str = ""
    prompt_template: PromptTemplate = field(init=False)

    def __post_init__(self):
        if self.prompt:
            self.prompt_template = PromptTemplate(self.prompt)
        else:
            self.prompt_template = PromptTemplate()
