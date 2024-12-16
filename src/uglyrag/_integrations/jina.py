from __future__ import annotations

import logging
from typing import Any

import requests

from uglyrag.config import Config

config = Config()
api_key = config.get("api_key", "JINA")
if api_key is None:
    raise ValueError("API 密钥未设置, 请修改 config.ini 文件，在 [JINA] 中设置 api_key=你的API密钥")


class JinaAPI:
    url = "https://api.jina.ai/v1"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    @classmethod
    def _request(cls, module: str, data: dict[str, Any], full_url: str | None = None) -> Any:
        if not data:
            logging.warning("Data is empty, skipping request.")
            return None

        try:
            if full_url is None:
                full_url = f"{cls.url}/{module}"
            logging.debug(f"Sending POST request to {full_url} with data: {data}")
            response = requests.post(full_url, headers=cls.headers, json=data)
            response.raise_for_status()  # 检查响应状态码
            logging.debug(f"Received response with status code: {response.status_code}")
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Request failed: {e}")
            return None

    @classmethod
    def embeddings(cls, texts: list[str]) -> list[list[float]]:
        data = {
            "model": "jina-embeddings-v3",
            "task": "text-matching",
            "late_chunking": False,
            "dimensions": 1024,
            "embedding_type": "float",
        }
        data["input"] = texts
        res = cls._request("embeddings", data)
        return [object["embedding"] for object in res["data"]]

    @classmethod
    def embedding(cls, text: str) -> list[float]:
        return cls.embeddings([text])[0]

    @classmethod
    def rerank(cls, query: str, documents: list[str]) -> list[float]:
        if not documents or not query:
            return []
        data = {
            "model": "jina-reranker-v2-base-multilingual",
            "query": query,
            "documents": documents,
            "top_n": len(documents),
        }
        res = cls._request("rerank", data)["results"]
        result = [0.0] * len(documents)
        for item in res:
            index = item.get("index")
            if index is not None and 0 <= index < len(documents):
                result[index] = item["relevance_score"]
        return result
