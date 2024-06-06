from dataclasses import dataclass
from typing import List, Optional

PROMPT_TEMPLATE = """
Answer the question in the same language as the question, based on the provided documents. Provide only the answer, without any additional text.
======
The following are provided documents:
```text
{reference}
```
======
Question:
```text
{question}
```
"""


@dataclass
class BasePromptTemplate:
    prompt_template = PROMPT_TEMPLATE

    def get_string(self, query: str, retrieval_results: Optional[List[str]] = None) -> str:
        if retrieval_results is None:
            return query
        return self.prompt_template.format(question=query, reference="\n".join(retrieval_results))
