"""LLM client — OpenAI when configured, otherwise mock."""
import logging

from app.config import settings
from utils.mock_llm import ask as mock_ask

logger = logging.getLogger(__name__)


def ask(question: str, history: list[dict] | None = None) -> tuple[str, int, int]:
    history = history or []

    if settings.openai_api_key:
        return _ask_openai(question, history)

    answer = mock_ask(question, history=history)
    input_tokens = max(1, len(question.split()) * 2)
    output_tokens = max(1, len(answer.split()) * 2)
    return answer, input_tokens, output_tokens


def _ask_openai(question: str, history: list[dict]) -> tuple[str, int, int]:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package is required when OPENAI_API_KEY is set") from exc

    client = OpenAI(api_key=settings.openai_api_key)
    messages = [
        {"role": m["role"], "content": m["content"]}
        for m in history[-settings.history_max_messages :]
    ]
    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        max_tokens=500,
    )
    answer = response.choices[0].message.content or ""
    usage = response.usage
    input_tokens = usage.prompt_tokens if usage else len(question.split()) * 2
    output_tokens = usage.completion_tokens if usage else len(answer.split()) * 2
    logger.info("OpenAI call model=%s in=%s out=%s", settings.llm_model, input_tokens, output_tokens)
    return answer, input_tokens, output_tokens
