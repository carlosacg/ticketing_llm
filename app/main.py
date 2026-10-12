import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.routes import health, tickets
from app.core.config import get_settings
from app.lifespan import lifespan
from app.llm.base import LLMError

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title=get_settings().app_name, lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(tickets.router)

    @app.exception_handler(LLMError)
    async def llm_error_handler(_: Request, exc: LLMError) -> JSONResponse:
        logger.warning("LLM analysis failed: %s", exc, exc_info=exc.__cause__)
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": "Ticket analysis failed, please try again later."},
        )

    return app


app = create_app()
