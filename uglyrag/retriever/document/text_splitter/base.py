from dataclasses import dataclass
from typing import Callable, List

from uglyrag import config

from .split_functions import SPLIT_FUNCTIONS
from .token import len_token


@dataclass
class TextSplitter:
    chunk_size: int = 1000
    chunk_overlap: int = 200
    length_function: callable = len_token

    def __post_init__(self) -> None:
        if self.chunk_overlap > self.chunk_size:
            raise ValueError("`chunk_overlap` must be less than `chunk_size`.")

    def split_text(self, text: str, split: Callable[str, List[str]] = SPLIT_FUNCTIONS[0]) -> List[str]:
        texts = []
        if self.chunk_size <= 0:
            return [text]
        parts: List[str] = split(text)
        part = ""
        i = 0
        while i < len(parts):
            part += parts[i]
            if self.length_function(part) + self.length_function(parts[i]) > self.chunk_size:
                if self.length_function(part) > self.chunk_size:
                    index = SPLIT_FUNCTIONS.index(split)
                    texts.extend(self.split_text(part, SPLIT_FUNCTIONS[index + 1]))
                else:
                    texts.append(part)
                part = ""
            i += 1

        if part:
            texts.append(part)
        return texts

    def split_documents(self, documents: List[str]) -> List[str]:
        """Split documents into chunks."""
        texts = []
        for document in documents:
            if self.length_function(document) <= self.chunk_size:
                texts.append(document)
                continue
            texts.extend(self.split_text(document))
        return texts


text_splitter = TextSplitter(chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap)
