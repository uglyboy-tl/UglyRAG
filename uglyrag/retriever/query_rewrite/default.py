from .base import BaseQueryRewrite


class DefaultQueryRewrite(BaseQueryRewrite):
    _name_ = "Default"

    def __call__(self, query: str) -> str:
        return query
