import anthropic

from app.core.config import Settings
from app.llm.base import LLMError
from app.llm.prompts import SYSTEM_PROMPT
from app.schemas.ticket import TicketAnalysis


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, settings: Settings) -> None:
        if not settings.anthropic_api_key:
            raise LLMError("ANTHROPIC_API_KEY is not configured")
        self.model = settings.anthropic_model
        self._effort = settings.anthropic_effort
        self._max_tokens = settings.anthropic_max_tokens
        self._client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )

    async def aclose(self) -> None:
        await self._client.close()

    async def analyze(self, description: str) -> TicketAnalysis:
        try:
            # Beta namespace for server-side fallbacks: if a safety classifier refuses,
            # the API retries on a fallback model instead of returning a refusal.
            response = await self._client.beta.messages.parse(
                model=self.model,
                max_tokens=self._max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": description}],
                output_format=TicketAnalysis,
                output_config={"effort": self._effort},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.APIConnectionError as exc:
            raise LLMError("Could not reach Anthropic API") from exc
        except anthropic.RateLimitError as exc:
            raise LLMError("Anthropic rate limit exceeded") from exc
        except anthropic.APIStatusError as exc:
            raise LLMError(f"Anthropic API error ({exc.status_code})") from exc

        if response.stop_reason == "refusal":
            raise LLMError("Anthropic refused to analyze the ticket")
        if response.stop_reason == "max_tokens":
            raise LLMError("Anthropic response was truncated (max_tokens)")
        if response.parsed_output is None:
            raise LLMError("Anthropic returned no structured output")
        return response.parsed_output
