import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.db.session import create_engine, create_session_factory
from app.llm.base import LLMError, LLMProvider
from app.llm.factory import build_llm_provider

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    engine = create_engine(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)

    llm_provider: LLMProvider | None
    try:
        llm_provider = build_llm_provider(settings)
    except LLMError as exc:
        # Start anyway so health/read endpoints work; analyze will answer 502.
        logger.warning("LLM provider '%s' disabled: %s", settings.llm_provider, exc)
        llm_provider = None
    app.state.llm_provider = llm_provider

    try:
        yield
    finally:
        if llm_provider is not None:
            await llm_provider.aclose()
        await engine.dispose()
