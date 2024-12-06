import logging

from uglyrag._search import SearchEngine

try:
    from uglyrag._utils._segment import segment

    SearchEngine.segment = segment
except ImportError as e:
    logging.warning(e)
    logging.warning("无法为 SearchEngine 引入分词模块")
    pass

try:
    from uglyrag._utils._embed import embeddings

    SearchEngine.embeddings = embeddings
except ImportError as e:
    logging.warning(e)
    logging.warning("无法为 SearchEngine 引入 embedding 模块")
    pass

try:
    from uglyrag._utils._rerank import rerank

    SearchEngine.rerank = rerank
except ImportError as e:
    logging.warning(e)
    logging.warning("无法为 SearchEngine 引入 rerank 模块")
    pass

__all__ = ["SearchEngine"]
__version__ = "0.1.0"
