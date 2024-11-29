import logging
import threading
from functools import wraps


# 单例修饰器
def singleton(cls):
    instances = {}  # 存储类的实例
    lock = threading.Lock()  # 锁对象，保证线程安全

    @wraps(cls)  # 保持原类的元数据
    def get_instance(*args, **kwargs):
        with lock:  # 保证线程同步
            if cls not in instances:
                logging.info(f"正在创建新的 {cls.__name__} 实例")
                instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
