from dataclasses import dataclass
from typing import List, Tuple

from cohere import Client

from uglyrag import config

from .base import BaseReranker


@dataclass
class Cohere_Reranker(BaseReranker):
    _name_ = "Cohere"

    def __post_init__(self):
        self.client = Client(config.cohere_api_key)
        self.model = config.cohere_model  # "rerank-english-v2.0"

    def __call__(self, query: str, contexts: List[str], top_n: int) -> List[Tuple[str, float]]:
        results = self.client.rerank(model=self.model, query=query, documents=contexts, top_n=top_n)
        return [(hit.document["text"], hit.relevance_score) for hit in results]
