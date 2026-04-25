from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from .config import settings


def get_claude() -> ChatAnthropic:
    return ChatAnthropic(
        model=settings.CLAUDE_MODEL,
        anthropic_api_key=settings.ANTHROPIC_API_KEY,
        temperature=0.3,
        max_tokens=4096,
    )


def get_gpt() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.GPT_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0.5,
    )
