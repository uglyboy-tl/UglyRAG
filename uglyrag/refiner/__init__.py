from .abstract import AbstractRefiner
from .base import Refiner


def get_refiner(name: str) -> Refiner:
    # 获取所有当前模块中的类
    subclasses = Refiner.__subclasses__()
    for subclass in subclasses:
        if subclass._name_ == name:
            return subclass()
    return None


__all__ = ["Refiner", "get_refiner"]
