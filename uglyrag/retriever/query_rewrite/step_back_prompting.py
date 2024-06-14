from .base import BaseQueryRewrite


class StepBackPromptingQueryRewrite(BaseQueryRewrite):
    _name_ = "Step-Back Prompting"

    def __call__(self, query: str) -> str:
        return query
