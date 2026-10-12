from app.llm.base import LLMProvider
from app.models.ticket import Ticket
from app.repositories.ticket_repository import TicketRepository


class TicketService:
    def __init__(self, repository: TicketRepository, llm: LLMProvider) -> None:
        self._repository = repository
        self._llm = llm

    async def analyze(self, description: str) -> Ticket:
        analysis = await self._llm.analyze(description)
        ticket = Ticket(
            description=description,
            category=analysis.category,
            severity=analysis.severity,
            summary=analysis.summary,
            recommended_actions=analysis.recommended_actions,
            llm_provider=self._llm.name,
            llm_model=self._llm.model,
        )
        return await self._repository.add(ticket)
