import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Category(StrEnum):
    DATABASE = "database"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    PERFORMANCE = "performance"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    OTHER = "other"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketAnalyzeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    description: str = Field(min_length=10, max_length=5000)


class TicketAnalysis(BaseModel):
    """Structured output contract shared by every LLM provider."""

    category: Category = Field(description="Area of the system the incident belongs to.")
    severity: Severity = Field(description="Business impact of the incident.")
    summary: str = Field(description="One or two sentence summary of the incident.")
    recommended_actions: list[str] = Field(
        description="Concrete, ordered steps an engineer should take next."
    )


class TicketAnalyzeResponse(TicketAnalysis):
    id: uuid.UUID


class TicketRead(TicketAnalysis):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    description: str
    llm_provider: str
    llm_model: str
    created_at: datetime
