import pytest
from pydantic import ValidationError

from app.schemas.ticket import TicketAnalysis


def test_ticket_analysis_rejects_invalid_category() -> None:
    with pytest.raises(ValidationError):
        TicketAnalysis.model_validate(
            {
                "category": "cooking",
                "severity": "high",
                "summary": "x",
                "recommended_actions": [],
            }
        )


def test_ticket_analysis_json_schema_is_closed_set() -> None:
    schema = TicketAnalysis.model_json_schema()

    assert set(schema["required"]) == {"category", "severity", "summary", "recommended_actions"}
    assert "critical" in schema["$defs"]["Severity"]["enum"]
