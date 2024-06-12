from dataclasses import dataclass
from typing import List, Optional

PROMPT_TEMPLATE = """
Answer the question based on the given document. Only give me the answer and do not output any other words.
======
The following are given documents.

{reference}

======
Question:
{question}
"""


@dataclass
class BasePromptTemplate:
    prompt_template: str = PROMPT_TEMPLATE

    def get_string(self, query: str, retrieval_results: Optional[List[str]] = None) -> str:
        if retrieval_results is None:
            retrieval_results = []
        return self.prompt_template.format(question=query, reference="\n".join(retrieval_results))
