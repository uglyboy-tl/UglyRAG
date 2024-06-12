from dataclasses import dataclass, field
from typing import List

import chromadb.utils.embedding_functions as embedding_functions
from chromadb import Client, Collection, PersistentClient
from loguru import logger

from uglyrag import config

from .base import Retriever

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=config.openai_embedding_api_key,
    model_name="text-embedding-3-small",
    api_base="https://openai-8ki.pages.dev/v1",
)


@dataclass
class Chroma(Retriever):
    collection_name: str = "chroma"
    persistent_path: str = "data/chroma"
    init_needed: bool = False
    client: Client = field(default_factory=Client)
    collection: Collection = field(init=False)

    def __post_init__(self):
        if self.persistent_path:
            self.client = PersistentClient(self.persistent_path)
        if self.init_needed:
            try:
                self.client.delete_collection(self.collection_name)
            except Exception:
                pass
        self.collection = self.client.get_or_create_collection(self.collection_name, embedding_function=openai_ef)

    def index(self, docs: List[str]):
        logger.info("正在构建索引(ChromaDB)...")
        self.collection.add(documents=docs, ids=[f"id{i}" for i in range(len(docs))])
        logger.success("索引构建完成")

    def search(self, query: str) -> List[str]:
        result = self.collection.query(
            query_texts=[query],
            n_results=self.topk,
            # where={"metadata_field": "is_equal_to_this"}, # optional filter
            # where_document={"$contains":"search_string"}  # optional filter
        )
        return result["documents"][0]
