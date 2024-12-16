from __future__ import annotations

import configparser
from unittest.mock import MagicMock

import pytest

from uglyrag.config import Config


# 创建一个Config对象的fixture
@pytest.fixture
def config(tmp_path):
    config = Config()
    config.config = MagicMock(spec=configparser.ConfigParser)
    config.config_path = tmp_path / "test_config.ini"
    config._changed = False  # 假设配置已更改，需要保存
    return config
