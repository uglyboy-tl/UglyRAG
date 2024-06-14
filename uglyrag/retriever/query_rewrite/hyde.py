from .base import BaseQueryRewrite


class HyDEQueryRewrite(BaseQueryRewrite):
    _name_ = "HyDE"

    def __call__(self, query: str) -> str:
        return query
