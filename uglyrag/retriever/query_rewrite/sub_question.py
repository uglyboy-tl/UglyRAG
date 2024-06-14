from .base import BaseQueryRewrite


class SubQuestionQueryRewrite(BaseQueryRewrite):
    _name_ = "Sub-Question"

    def __call__(self, query: str) -> str:
        return query
