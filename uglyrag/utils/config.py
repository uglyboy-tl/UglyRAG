#!/usr/bin/env python3

import os
from dataclasses import dataclass

from .singleton import singleton


@singleton
@dataclass
class Config:
    # API keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    openai_api_base: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")


config = Config()
