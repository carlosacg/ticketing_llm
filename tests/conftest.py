from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import create_app
from app.schemas.ticket import Category, Severity, TicketAnalysis

FAKE_ANALYSIS = TicketAnalysis(
    category=Category.DATABASE,
    severity=Severity.HIGH,
    summary="Checkout service cannot reach the primary database.",
    recommended_actions=["Check DB connection pool", "Inspect DB server load"],
)


class FakeLLMProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self, result: TicketAnalysis | Exception = FAKE_ANALYSIS) -> None:
        self.result = result
        self.calls: list[str] = []

    async def analyze(self, description: str) -> TicketAnalysis:
        self.calls.append(description)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result

    async def aclose(self) -> None:
        pass


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
def fake_llm() -> FakeLLMProvider:
    return FakeLLMProvider()


@pytest.fixture
def app(session_factory: async_sessionmaker[AsyncSession], fake_llm: FakeLLMProvider) -> FastAPI:
    # ASGITransport does not run the lifespan, so set the state it would provide.
    app = create_app()
    app.state.session_factory = session_factory
    app.state.llm_provider = fake_llm
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
