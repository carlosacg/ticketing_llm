from typing import Protocol

from app.schemas.ticket import TicketAnalysis


class LLMError(Exception):
    """Raised when the LLM provider fails to return a valid analysis."""


class LLMProvider(Protocol):
    name: str
    model: str

    async def analyze(self, description: str) -> TicketAnalysis: ...

    async def aclose(self) -> None: ...
