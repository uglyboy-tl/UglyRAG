import tiktoken


def len_token(text: str, model: str = "gpt-4-0613"):
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(text)) + 6
    return num_tokens
