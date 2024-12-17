from __future__ import annotations

import logging

from uglyrag.search import SearchEngine


def import_module(module_name: str, attribute_name: str, target: object, warning_message: str) -> None:
    try:
        module = __import__(module_name, fromlist=[attribute_name])
        attribute = getattr(module, attribute_name, None)
        if attribute is not None:
            setattr(target, attribute_name, attribute)
    except ImportError as e:
        logging.debug(e)
        logging.warning(warning_message)


import_module("uglyrag.modules._segment", "segment", SearchEngine, "未引入分词模块，拉丁语系不受影响")
import_module("uglyrag.modules._embed", "embeddings", SearchEngine, "无法为 SearchEngine 引入 embedding 模块")
import_module("uglyrag.modules._rerank", "rerank", SearchEngine, "未引入 rerank 模块，将使用混合搜索策略")
import_module("uglyrag.modules._split", "split", SearchEngine, "未引入 split 模块，导入的文章不会被分割")

__all__ = ["SearchEngine"]
__version__ = "0.1.0"
