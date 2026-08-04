from fastapi import FastAPI

from app.core.config import Settings, get_settings
from app.core.cors import register_cors_middleware
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.rate_limit import register_rate_limit_middleware
from app.middleware.tracing import register_trace_middleware
from app.routers import chat, evaluation, health, knowledge_base, rag, tickets, tools


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
    )
    register_exception_handlers(app)
    register_trace_middleware(app)
    register_rate_limit_middleware(app, settings)
    register_cors_middleware(app, settings.cors_allowed_origin_list)
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(knowledge_base.router)
    app.include_router(rag.router)
    app.include_router(evaluation.router)
    app.include_router(tools.router)
    app.include_router(tickets.router)
    return app


app = create_app()
