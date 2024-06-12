from dataclasses import dataclass, field
from typing import List, Optional

from loguru import logger

from uglyrag.generator import Generator, OpenAI_Generator
from uglyrag.judger import Judger
from uglyrag.refiner import Refiner
from uglyrag.retriever import Reranker, Retriever


@dataclass
class BasicPipeline:
    retriever: Optional[Retriever] = None
    generator: Generator = field(default_factory=lambda: OpenAI_Generator())
    judger: Optional[Judger] = None
    reranker: Optional[Reranker] = None
    refiner: Optional[Refiner] = None

    def __post_init__(self):
        pass

    def process(self, query: str, docs: Optional[List[str]] = None) -> str:
        """
        Run the pipeline.
        """
        if self.judger and not self.judger(query) or not self.retriever:
            logger.debug("无需检索或无法检索，将直接生成答案...")
            result = self.generator(query)
            logger.success(f"{result}")
            return result

        if docs:
            self.retriever.index(docs)

        logger.info("正在检索...")
        contexts = self.retriever.search(query)
        logger.success(f"检索到 {len(contexts)} 条结果。")
        formatted_lines = "\n".join([f"{index + 1}. {line}" for index, line in enumerate(contexts)])
        logger.debug(f"检索结果如下:\n{formatted_lines}")

        if self.reranker:
            logger.info("正在重新排序...")
            contexts, scores = self.reranker(query, contexts)

        if self.refiner:
            logger.info("正在精简...")
            contexts = self.refiner(query, contexts)

        logger.info("正在生成答案...")
        result = self.generator(query, contexts)
        logger.success(f"{result}")
        return result
