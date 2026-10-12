from app.core.config import Settings
from app.llm.base import LLMProvider


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "openai":
        from app.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(settings)

    from app.llm.anthropic_provider import AnthropicProvider

    return AnthropicProvider(settings)
