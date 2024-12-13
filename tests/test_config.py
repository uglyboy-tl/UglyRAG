from __future__ import annotations

from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, StreamHandler

import pytest

from uglyrag._config import configure_logger, singleton


# 测试用的简单类，用于验证singleton装饰器
@singleton
class TestSingletonClass:
    def __init__(self, value):
        self.value = value


def test_singleton_creation():
    # 测试实例的创建
    instance1 = TestSingletonClass(10)
    instance2 = TestSingletonClass(10)

    # 验证是否为同一个实例
    assert instance1 is instance2
    assert instance1.value == instance2.value


def test_singleton_different_args():
    # 使用不同的参数实例化类，验证是否仍然为同一个实例
    instance1 = TestSingletonClass(10)
    instance2 = TestSingletonClass(20)

    assert instance1 is instance2
    assert instance1.value == instance2.value


def test_configure_logger_level():
    logger = StreamHandler()
    configure_logger(logger, "DEBUG")
    assert logger.level == DEBUG

    configure_logger(logger, "INFO")
    assert logger.level == INFO

    configure_logger(logger, "WARNING")
    assert logger.level == WARNING

    configure_logger(logger, "ERROR")
    assert logger.level == ERROR

    configure_logger(logger, "CRITICAL")
    assert logger.level == CRITICAL

    configure_logger(logger, "INVALID_LEVEL")
    assert logger.level == INFO
