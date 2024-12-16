from __future__ import annotations

import logging
import threading
from typing import Any, cast

from uglyrag.singleton import singleton

# 配置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("TestSingletonClass")


# 测试用的简单类，用于验证singleton装饰器
@singleton
class TestSingletonClass:
    def __init__(self, value):
        self.value = value


@singleton
class TestSingletonExceptionClass:
    def __init__(self, value):
        if value < 0:
            raise ValueError("Value must be non-negative")
        self.value = value


def reset_singleton():
    cast(Any, TestSingletonClass).reset_instance()
    cast(Any, TestSingletonExceptionClass).reset_instance()


def test_singleton_creation():
    reset_singleton()
    # 测试实例的创建
    instance1 = TestSingletonClass(10)
    instance2 = TestSingletonClass(10)

    # 验证是否为同一个实例
    assert instance1 is instance2
    assert instance1.value == instance2.value


def test_singleton_different_args():
    reset_singleton()
    # 使用不同的参数实例化类，验证是否仍然为同一个实例
    instance1 = TestSingletonClass(10)
    instance2 = TestSingletonClass(20)

    assert instance1 is instance2
    assert instance1.value == instance2.value


def test_singleton_multithreading():
    reset_singleton()

    # 测试多线程环境下的单例模式
    def create_instance():
        return TestSingletonClass(30)

    thread1 = threading.Thread(target=create_instance)
    thread2 = threading.Thread(target=create_instance)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    instance1 = create_instance()
    instance2 = create_instance()

    assert instance1 is instance2
    assert instance1.value == instance2.value


def test_singleton_exception():
    reset_singleton()
    # 测试在实例化过程中抛出异常的情况
    try:
        TestSingletonExceptionClass(-1)
    except ValueError:
        pass

    instance1 = TestSingletonExceptionClass(10)
    instance2 = TestSingletonExceptionClass(20)

    assert instance1 is instance2
    assert instance1.value == instance2.value
    assert instance1.value == 10


def test_singleton_logging(caplog):
    reset_singleton()
    # 测试单例类的日志记录功能
    with caplog.at_level(logging.DEBUG):
        instance1 = TestSingletonClass(30)
        instance2 = TestSingletonClass(40)

    assert instance1 is instance2
    assert instance2.value == 30
    assert "尝试创建新的 TestSingletonClass 实例" in caplog.text
    assert "成功创建新的 TestSingletonClass 实例" in caplog.text
