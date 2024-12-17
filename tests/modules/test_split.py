from __future__ import annotations

import pytest

from uglyrag.modules.split import get_split_module


def test_invalid_module(mock_config):
    mock_config.split_module = "InvalidModule"
    with pytest.raises(ImportError, match="No such split module: InvalidModule"):
        get_split_module()


def test_no_module_configured(mock_config):
    mock_config.split_module = ""
    with pytest.raises(ImportError, match="未配置 split 模块"):
        get_split_module()


@pytest.mark.parametrize("module_name", ["REGEX"])
def test_valid_modules(mock_config, module_name):
    mock_config.split_module = module_name
    split = get_split_module()

    assert split is not None, "split should be imported correctly"
    result = split("测试文本")
    assert isinstance(result, list), "Result should be a list"
    assert all(isinstance(item, tuple) for item in result), "Each item in result should be a tuple"
    assert all(len(item) == 2 for item in result), "Each tuple should have two elements"
    assert all(
        isinstance(item[0], str) and isinstance(item[1], str) for item in result
    ), "Each element in tuple should be a string"
