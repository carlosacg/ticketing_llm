import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.depends import TicketRepositoryDep, TicketServiceDep
from app.schemas.ticket import (
    Category,
    Severity,
    TicketAnalyzeRequest,
    TicketAnalyzeResponse,
    TicketRead,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post(
    "/analyze",
    response_model=TicketAnalyzeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_ticket(
    payload: TicketAnalyzeRequest,
    service: TicketServiceDep,
) -> TicketAnalyzeResponse:
    ticket = await service.analyze(payload.description)
    return TicketAnalyzeResponse.model_validate(ticket, from_attributes=True)


@router.get("", response_model=list[TicketRead])
async def list_tickets(
    repository: TicketRepositoryDep,
    category: Category | None = None,
    severity: Severity | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TicketRead]:
    tickets = await repository.list(
        category=category, severity=severity, limit=limit, offset=offset
    )
    return [TicketRead.model_validate(t) for t in tickets]


@router.get("/{ticket_id}", response_model=TicketRead)
async def get_ticket(ticket_id: uuid.UUID, repository: TicketRepositoryDep) -> TicketRead:
    ticket = await repository.get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return TicketRead.model_validate(ticket)
