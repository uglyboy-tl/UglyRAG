from __future__ import annotations

import configparser
from unittest.mock import MagicMock

import pytest

from uglyrag.config import Config
from uglyrag.config import config as cfg

JINA_TEST_API_KEY = "jina_d2ea2a2b72cd4cd4bad16b96b3e340aeZ1Ae5BHHSXXbHqDUUe0-TlNrBJbY"


# 创建一个Config对象的fixture
@pytest.fixture
def config(tmp_path):
    config = Config()
    config.config = MagicMock(spec=configparser.ConfigParser)
    config.config_path = tmp_path / "test_config.ini"
    config._changed = False  # 假设配置已更改，需要保存
    return config


@pytest.fixture
def mock_config(monkeypatch):
    class MockConfig:
        def __init__(self):
            self.embedding_module = ""
            self.rerank_module = ""
            self.segment_module = ""
            self.split_module = ""

        def get(self, option: str, section: str = "DEFAULT", default: str = "") -> str:
            if section == "MODULES" and option == "embedding":
                return self.embedding_module
            elif section == "MODULES" and option == "rerank":
                return self.rerank_module
            elif section == "MODULES" and option == "segment":
                return self.segment_module
            elif section == "MODULES" and option == "split":
                return self.split_module
            elif section == "JINA" and option == "api_key":
                return JINA_TEST_API_KEY
            return default

        def __str__(self):
            return f"MockConfig(embedding_module={self.embedding_module}, rerank_module={self.rerank_module}, segment_module={self.segment_module}, split_module={self.split_module})"

    config = MockConfig()
    monkeypatch.setattr(cfg, "get", config.get)
    return config
