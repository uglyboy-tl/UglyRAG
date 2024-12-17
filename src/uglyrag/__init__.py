from __future__ import annotations

from uglyrag.db_manager import DatabaseManager
from uglyrag.modules.embed import get_embeddings_module
from uglyrag.modules.rerank import get_rerank_module
from uglyrag.modules.segment import get_segment_module
from uglyrag.modules.split import get_split_module
from uglyrag.search import SearchEngine
from uglyrag.utils import load_module

load_module(get_segment_module, "segment", DatabaseManager, "未引入分词模块，拉丁语系不受影响")
load_module(get_embeddings_module, "embeddings", DatabaseManager, "无法为 SearchEngine 引入 embedding 模块")
load_module(get_rerank_module, "rerank", SearchEngine, "未引入 rerank 模块，将使用混合搜索策略")
load_module(get_split_module, "split", SearchEngine, "未引入 split 模块，导入的文章不会被分割")

__all__ = ["SearchEngine"]
__version__ = "0.1.0"
