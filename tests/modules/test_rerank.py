from __future__ import annotations

import pytest

from uglyrag.modules.rerank import get_rerank_module


def test_invalid_module(mock_config):
    mock_config.rerank_module = "InvalidModule"
    with pytest.raises(ImportError, match="No such rerank module: InvalidModule"):
        get_rerank_module()


def test_no_module_configured(mock_config):
    mock_config.rerank_module = ""
    with pytest.raises(ImportError, match="未配置 rerank 模块"):
        get_rerank_module()


@pytest.mark.parametrize("module_name", ["JINA"])
def test_valid_modules(mock_config, module_name):
    mock_config.rerank_module = module_name
    rerank = get_rerank_module()

    assert rerank is not None, "rerank should be imported correctly"
    result = rerank("query", ["doc1", "doc2"])
    assert isinstance(result, list), "Result should be a list"
    assert all(isinstance(score, float) for score in result), "Each score in result should be a float"
