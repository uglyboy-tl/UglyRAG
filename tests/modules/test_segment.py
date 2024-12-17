from __future__ import annotations

import pytest

from uglyrag.modules.segment import get_segment_module


def test_invalid_module(mock_config):
    mock_config.segment_module = "InvalidModule"
    with pytest.raises(ImportError, match="No such segment module: InvalidModule"):
        get_segment_module()


def test_no_module_configured(mock_config):
    mock_config.segment_module = ""
    with pytest.raises(ImportError, match="未配置 segment 模块"):
        get_segment_module()


@pytest.mark.parametrize("module_name", ["Jieba"])
def test_valid_modules(mock_config, module_name):
    mock_config.segment_module = module_name
    segment = get_segment_module()

    assert segment is not None, "segment should be imported correctly"
    result = segment("测试文本")
    assert isinstance(result, list), "Result should be a list"
    assert all(isinstance(item, str) for item in result), "Each item in result should be a string"
