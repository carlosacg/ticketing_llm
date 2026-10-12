import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket
from app.schemas.ticket import Category, Severity


class TicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, ticket: Ticket) -> Ticket:
        self._session.add(ticket)
        await self._session.commit()
        await self._session.refresh(ticket)
        return ticket

    async def get(self, ticket_id: uuid.UUID) -> Ticket | None:
        return await self._session.get(Ticket, ticket_id)

    async def list(
        self,
        *,
        category: Category | None = None,
        severity: Severity | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Ticket]:
        stmt = select(Ticket).order_by(Ticket.created_at.desc()).limit(limit).offset(offset)
        if category is not None:
            stmt = stmt.where(Ticket.category == category)
        if severity is not None:
            stmt = stmt.where(Ticket.severity == severity)
        result = await self._session.scalars(stmt)
        return list(result)
