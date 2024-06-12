from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from uglyrag.generator import Generator, OpenAI_Generator

from .base import Judger

PROMPT_TEMPLATE = """
I will provide a question. Please determine if this question can be directly answered by the model or if additional information needs to be retrieved to help answer it. Respond with either 'Yes' or 'No' only, without any additional information.
======
## Question:
{question}

## Answer:
"""


@dataclass
class LLM_Judger(Judger):
    generator: Generator = field(init=False)

    def __post_init__(self) -> None:
        self.generator = OpenAI_Generator(PROMPT_TEMPLATE)

    def __call__(self, query: str) -> Optional[str]:
        result = self.generator(query)
        logger.trace(f"Judger result: {result}")
        if result.lower() == "yes":
            return None
        return [self.generator(query)]
