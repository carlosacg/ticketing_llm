import openai

from app.core.config import Settings
from app.llm.base import LLMError
from app.llm.prompts import SYSTEM_PROMPT
from app.schemas.ticket import TicketAnalysis


class OpenAIProvider:
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise LLMError("OPENAI_API_KEY is not configured")
        self.model = settings.openai_model
        self._client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )

    async def aclose(self) -> None:
        await self._client.close()

    async def analyze(self, description: str) -> TicketAnalysis:
        try:
            response = await self._client.responses.parse(
                model=self.model,
                instructions=SYSTEM_PROMPT,
                input=description,
                text_format=TicketAnalysis,
            )
        except openai.APIConnectionError as exc:
            raise LLMError("Could not reach OpenAI API") from exc
        except openai.RateLimitError as exc:
            raise LLMError("OpenAI rate limit exceeded") from exc
        except openai.APIStatusError as exc:
            raise LLMError(f"OpenAI API error ({exc.status_code})") from exc

        if response.output_parsed is None:
            raise LLMError("OpenAI returned no structured output (refusal or incomplete)")
        return response.output_parsed
