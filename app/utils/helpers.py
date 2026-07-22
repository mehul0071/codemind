import logging
from typing import Optional
import tiktoken

logger = logging.getLogger("codemind")


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    try:
        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text) / 3.5))


def truncate_to_token_budget(text: str, max_tokens: int, model: str = "gpt-3.5-turbo") -> str:
    try:
        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return enc.decode(tokens[:max_tokens])
    except ImportError:
        approx_chars = int(max_tokens * 3.5)
        return text[:approx_chars]


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logging.basicConfig(
        level=level,
        format='{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","msg":%(message)s}',
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    return logging.getLogger("codemind")
