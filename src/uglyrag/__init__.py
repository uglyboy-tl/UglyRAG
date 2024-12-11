from __future__ import annotations

import logging

from uglyrag._search import SearchEngine

try:
    from uglyrag._modules._segment import segment

    if segment is not None:
        SearchEngine.segment = segment
except ImportError as e:
    logging.debug(e)
    logging.warning("未引入分词模块，拉丁语系不受影响")
    pass

try:
    from uglyrag._modules._embed import embeddings

    if embeddings is not None:
        SearchEngine.embeddings = embeddings
except ImportError as e:
    logging.debug(e)
    logging.warning("无法为 SearchEngine 引入 embedding 模块")
    pass

try:
    from uglyrag._modules._rerank import rerank

    if rerank is not None:
        SearchEngine.rerank = rerank
except ImportError as e:
    logging.debug(e)
    logging.warning("未引入 rerank 模块，将使用混合搜索策略")
    pass

try:
    from uglyrag._modules._split import split

    SearchEngine.split = split
except ImportError as e:
    logging.debug(e)
    logging.warning("未引入 split 模块，导入的文章不会被分割")
    pass

__all__ = ["SearchEngine"]
__version__ = "0.1.0"
