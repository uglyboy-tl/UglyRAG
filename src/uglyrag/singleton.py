from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

T = TypeVar("T")


# 单例修饰器
def singleton(cls: type[T]) -> Callable[..., T]:
    instances = {}
    lock = threading.Lock()  # 锁对象，保证线程安全

    @wraps(cls)  # 保持原类的元数据
    def get_instance(*args: Any, **kwargs: Any) -> T:
        logger = logging.getLogger(cls.__name__)
        if cls not in instances:
            with lock:  # 保证线程同步
                if cls not in instances:
                    try:
                        logger.debug(f"尝试创建新的 {cls.__name__} 实例")
                        instance = cls(*args, **kwargs)
                        logger.info(f"成功创建新的 {cls.__name__} 实例")
                        instances[cls] = instance
                    except Exception as e:
                        logger.error(f"创建 {cls.__name__} 实例时发生错误: {e}")
                        raise
        return instances[cls]

    def reset_instance() -> None:
        with lock:
            instances.pop(cls, None)

    get_instance.reset_instance = reset_instance  # type: ignore
    return get_instance
