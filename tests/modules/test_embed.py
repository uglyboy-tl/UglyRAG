from __future__ import annotations

import pytest

from uglyrag.modules.embed import get_embeddings_module


def test_invalid_module(mock_config):
    mock_config.embedding_module = "InvalidModule"
    print(f"mock_config.get('embedding', 'MODULES', 'JINA') = {mock_config.get('embedding', 'MODULES', 'JINA')}")
    print(f"test_invalid_module: mock_config = {mock_config}")
    with pytest.raises(ImportError, match="No such embedding module: InvalidModule"):
        get_embeddings_module()


def test_no_module_configured(mock_config):
    mock_config.embedding_module = ""
    with pytest.raises(ImportError, match="未配置 embedding 模块"):
        get_embeddings_module()


@pytest.mark.parametrize("module_name", ["FastEmbed", "JINA"])
def test_valid_modules(mock_config, module_name):
    mock_config.embedding_module = module_name
    embeddings = get_embeddings_module()

    assert embeddings is not None, "embeddings should be imported correctly"
    result = embeddings(["test"])
    assert isinstance(result, list), "Result should be a list"
    assert all(isinstance(list(item), list) for item in result), "Each item in result should be a list"
