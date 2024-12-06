import requests

from uglyrag._config import Config

config = Config()
api_key = config.get("api_key", "JINA")
if api_key is None:
    raise ValueError("API 密钥未设置, 请修改 config.ini 文件，在 [JINA] 中设置 api_key=你的API密钥")

data = {
    "model": "jina-embeddings-v3",
    "task": "text-matching",
    "late_chunking": False,
    "dimensions": 1024,
    "embedding_type": "float",
}


class JinaAPI:
    url = "https://api.jina.ai/v1"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    @classmethod
    def _request(cls, module: str, data: dict):
        return requests.post(f"{cls.url}/{module}", headers=cls.headers, json=data)

    @classmethod
    def embeddings(cls, texts: list):
        data = {
            "model": "jina-embeddings-v3",
            "task": "text-matching",
            "late_chunking": False,
            "dimensions": 1024,
            "embedding_type": "float",
        }
        data["input"] = texts
        res = cls._request("embeddings", data)
        return [str(object["embedding"]) for object in res.json()["data"]]

    @classmethod
    def rerank(cls, query: str, documents: list, top_n: int):
        data["model"] = "jina-reranker-v2-base-multilingual"
        data["query"] = query
        data["docs"] = documents
        data["top_n"] = top_n
        res = cls._request("rerank", data)
        return res.json()["results"]
