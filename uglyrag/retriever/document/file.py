from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from loguru import logger
from unstructured.partition.auto import partition

from .base import BaseDocument
from .text_splitter import text_splitter


@dataclass
class FileDocument(BaseDocument):
    path: Path = field(init=False)
    _name_ = "File"

    def __post_init__(self):
        self.path = Path(self.doc)
        assert self.path.exists()
        self.elements = partition(self.path)

    @property
    def indexed_contents(self) -> List[str]:
        filename = self.path.name
        return [filename + "\n\n" + content for content in self.original_contents]

    @property
    def original_contents(self) -> List[str]:
        if not hasattr(self, "_original_contents"):
            logger.debug(f"正在解析文件 {self.path} ...")
            elements = partition(self.path)
            content = "\n\n".join([str(element) for element in elements])
            self._original_contents = text_splitter.split_text(content)
            logger.debug(f"文件 {self.path} 解析完成，共 {len(self._original_contents)} 段")
        assert isinstance(self._original_contents, list)
        return self._original_contents
