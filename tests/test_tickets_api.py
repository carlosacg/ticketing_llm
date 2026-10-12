import uuid

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.core.config import Settings
from app.lifespan import lifespan
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.base import LLMError
from app.llm.openai_provider import OpenAIProvider
from tests.conftest import FAKE_ANALYSIS, FakeLLMProvider

DESCRIPTION = "Database connection timeout on the checkout service since 10:00 UTC."


async def test_analyze_returns_structured_analysis(
    client: AsyncClient, fake_llm: FakeLLMProvider
) -> None:
    response = await client.post("/tickets/analyze", json={"description": DESCRIPTION})

    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "database"
    assert body["severity"] == "high"
    assert body["summary"] == FAKE_ANALYSIS.summary
    assert body["recommended_actions"] == FAKE_ANALYSIS.recommended_actions
    assert uuid.UUID(body["id"])
    assert fake_llm.calls == [DESCRIPTION]


async def test_analyze_persists_ticket(client: AsyncClient) -> None:
    created = (await client.post("/tickets/analyze", json={"description": DESCRIPTION})).json()

    response = await client.get(f"/tickets/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["description"] == DESCRIPTION
    assert body["llm_provider"] == "fake"
    assert body["llm_model"] == "fake-model"
    assert body["created_at"]


async def test_analyze_rejects_short_description(
    client: AsyncClient, fake_llm: FakeLLMProvider
) -> None:
    response = await client.post("/tickets/analyze", json={"description": "   "})

    assert response.status_code == 422
    assert fake_llm.calls == []


async def test_analyze_returns_502_when_llm_fails(
    client: AsyncClient, fake_llm: FakeLLMProvider
) -> None:
    fake_llm.result = LLMError("boom")

    response = await client.post("/tickets/analyze", json={"description": DESCRIPTION})

    assert response.status_code == 502
    assert "boom" not in response.text
    assert (await client.get("/tickets")).json() == []


async def test_list_tickets_filters(client: AsyncClient, fake_llm: FakeLLMProvider) -> None:
    await client.post("/tickets/analyze", json={"description": DESCRIPTION})
    fake_llm.result = FAKE_ANALYSIS.model_copy(update={"category": "network", "severity": "low"})
    await client.post("/tickets/analyze", json={"description": "DNS resolution flaky in staging"})

    all_tickets = (await client.get("/tickets")).json()
    network = (await client.get("/tickets", params={"category": "network"})).json()
    high = (await client.get("/tickets", params={"severity": "high"})).json()

    assert len(all_tickets) == 2
    assert [t["category"] for t in network] == ["network"]
    assert [t["severity"] for t in high] == ["high"]


async def test_list_tickets_rejects_unknown_category(client: AsyncClient) -> None:
    response = await client.get("/tickets", params={"category": "bogus"})

    assert response.status_code == 422


async def test_get_ticket_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/tickets/{uuid.uuid4()}")

    assert response.status_code == 404


def test_provider_requires_api_key() -> None:
    settings = Settings(anthropic_api_key="", openai_api_key="", _env_file=None)
    for provider_cls in (AnthropicProvider, OpenAIProvider):
        with pytest.raises(LLMError, match="API_KEY is not configured"):
            provider_cls(settings)


async def test_analyze_returns_502_when_provider_not_configured(
    app: FastAPI, client: AsyncClient
) -> None:
    app.state.llm_provider = None

    response = await client.post("/tickets/analyze", json={"description": DESCRIPTION})

    assert response.status_code == 502


async def test_lifespan_starts_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        llm_provider="anthropic",
        anthropic_api_key="",
        database_url="sqlite+aiosqlite://",
        _env_file=None,
    )
    monkeypatch.setattr("app.lifespan.get_settings", lambda: settings)
    app = FastAPI()

    async with lifespan(app):
        assert app.state.llm_provider is None
        assert app.state.session_factory is not None
