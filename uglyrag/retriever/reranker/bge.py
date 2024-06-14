# -*- coding: utf-8 -*-
# modified from repo: https://github.com/percent4/embedding_rerank_retrieval
# @place: Pudong, Shanghai
# @file: rerank.py
# @time: 2023/12/26 19:21
import json
from dataclasses import dataclass
from typing import List, Tuple

import requests

from .base import BaseReranker


@dataclass
class BGE_Reranker(BaseReranker):
    _name_ = "BGE"

    def __call__(self, query: str, contexts: List[str], top_n: int) -> List[Tuple[str, float]]:
        url = "http://localhost:50072/bge_large_rerank"
        payload = json.dumps({"query": query, "passages": contexts, "top_k": top_n})
        headers = {"Content-Type": "application/json"}

        response = requests.request("POST", url, headers=headers, data=payload)
        return list(response.json().items())
