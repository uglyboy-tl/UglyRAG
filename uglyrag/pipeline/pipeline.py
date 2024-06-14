from dataclasses import dataclass, field
from typing import Dict, List, Optional

from loguru import logger

from uglyrag.generator import LLM, Generator, get_generator_class
from uglyrag.judger import Judger, get_judger
from uglyrag.refiner import Refiner, get_refiner
from uglyrag.retriever import Retriever, get_retriever_class


@dataclass
class BasicPipeline:
    retriever: Optional[Retriever] = None
    config: Dict[str, str] = field(default_factory=dict)
    generator: Generator = field(init=False)
    judger: Optional[Judger] = field(init=False)
    refiner: Optional[Refiner] = field(init=False)

    def __post_init__(self):
        retriever_type = get_retriever_class(self.config.get("retriever", "None"))
        if not self.retriever and retriever_type is not None:
            self.retriever = retriever_type()
        generator_type = get_generator_class(self.config.get("generator", "OpenAI"))
        if issubclass(generator_type, LLM):
            self.generator = generator_type(prompt=self.config.get("generator_prompt", ""))
            logger.debug(f"Using {self.generator._name_} as LLM")
        else:
            self.generator = generator_type()
        self.judger = get_judger(self.config.get("judger", "None"))
        self.refiner = get_refiner(self.config.get("refiner", "None"))

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

        if self.refiner:
            logger.info("正在精简...")
            contexts = self.refiner(query, contexts)

        logger.info("正在生成答案...")
        result = self.generator(query, contexts)
        logger.success(f"{result}")
        return result
