from typing import List

punt_list = {"?", "!", ";", "？", "！", "。", "；", "……", "…", "\n"}


def cut_sentences(text: str) -> List[str]:
    """
    Split the text into sentences, keeping the original punctuation.
    """
    sentences = [text]
    for sep in punt_list:
        text_list, sentences = sentences, []
        for seq in text_list:
            parts = seq.split(sep)
            for part in parts[:-1]:
                if part:
                    sentences.append(part + sep)
            if parts[-1]:  # Handle the last part separately to avoid adding an extra separator
                sentences.append(parts[-1])
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    return sentences


SPLIT_FUNCTIONS = [
    cut_sentences,
    lambda text: text.split(" "),
    lambda text: list(text),
]
