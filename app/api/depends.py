from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.llm.base import LLMError, LLMProvider
from app.repositories.ticket_repository import TicketRepository
from app.services.ticket_service import TicketService

SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_llm_provider(request: Request) -> LLMProvider:
    provider: LLMProvider | None = request.app.state.llm_provider
    if provider is None:
        raise LLMError("LLM provider is not configured")
    return provider


LLMProviderDep = Annotated[LLMProvider, Depends(get_llm_provider)]


def get_ticket_repository(session: SessionDep) -> TicketRepository:
    return TicketRepository(session)


TicketRepositoryDep = Annotated[TicketRepository, Depends(get_ticket_repository)]


def get_ticket_service(repository: TicketRepositoryDep, llm: LLMProviderDep) -> TicketService:
    return TicketService(repository, llm)


TicketServiceDep = Annotated[TicketService, Depends(get_ticket_service)]
