from typing import List

punt_list = {"?", "!", ";", "？", "！", "。", "；", "……", "…", "\n"}


def cut_sentences(text: str) -> List[str]:
    """
    Split the text into sentences.
    """
    sentences = [text]
    for sep in punt_list:
        text_list, sentences = sentences, []
        for seq in text_list:
            sentences += seq.split(sep)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    return sentences


SPLIT_FUNCTIONS = [
    cut_sentences,
    lambda text: text.split(" "),
    lambda text: list(text),
]
