from dataclasses import dataclass
from typing import List, Optional

from loguru import logger
from openai import OpenAI

from uglyrag import config

from .base import LLM, Generator


@dataclass
class OpenAI_Generator(LLM, Generator):
    _name_ = "OpenAI"
    api_key: str = config.openai_api_key
    base_url: str = config.openai_api_base
    model: str = config.openai_model

    def __post_init__(self):
        LLM.__post_init__(self)
        if self.api_key is None:
            raise ValueError("OPENAI_API_KEY is not set")

    def __call__(self, query: str, retrieval_results: Optional[List[str]] = None) -> str:
        input_prompt = self.prompt_template.get_string(query, retrieval_results)
        logger.trace(input_prompt)
        return self.generator(input_prompt)

    def generator(self, input_prompt: str) -> str:
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": input_prompt,
                }
            ],
            model=self.model,
        )
        return chat_completion.choices[0].message.content
