from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.observability import setup_logging
from .routers import (
    health,
    auth,
    projects,
    jobs,
    documents,
    export,
    glossary,
    terms_suggest,
    downloads,
    assets,
    batch,
    health_observability,
    metrics,
    settings as settings_router,
    websocket as websocket_router,
)


def create_app() -> FastAPI:
    setup_logging(json_logs=bool(getattr(settings, "log_json", False)))
    app = FastAPI(
        title="AxiomFlow API",
        version="0.1.0",
        description="Backend API for AxiomFlow scientific PDF translation web app.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router, prefix="/v1")
    app.include_router(auth.router, prefix="/v1")
    app.include_router(projects.router, prefix="/v1")
    app.include_router(glossary.router, prefix="/v1")
    app.include_router(jobs.router, prefix="/v1")
    app.include_router(documents.router, prefix="/v1")
    app.include_router(assets.router, prefix="/v1")
    app.include_router(assets.assets_router, prefix="/v1")
    app.include_router(terms_suggest.router, prefix="/v1")
    app.include_router(export.router, prefix="/v1")
    app.include_router(downloads.router, prefix="/v1")
    app.include_router(batch.router, prefix="/v1")
    app.include_router(settings_router.router, prefix="/v1")
    app.include_router(health_observability.router, prefix="/v1")
    app.include_router(metrics.router, prefix="/v1")
    app.include_router(websocket_router.router, prefix="/v1")

    return app


app = create_app()


