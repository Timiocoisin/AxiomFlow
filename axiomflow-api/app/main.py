from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# 尽早加载 .env（将其注入到 os.environ，便于直接使用 os.getenv）
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

from .core.config import settings
from .core.observability import setup_logging
from .routers import (
    health,
    auth,
    users,
    projects,
    jobs,
    documents,
    export,
    glossary,
    terms_suggest,
    downloads,
    assets,
    batch,
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
        # 开发环境允许任意端口的 localhost/127.0.0.1（避免端口变化导致 CORS 被拒）
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static files for user-uploaded content (e.g., avatars)
    static_dir = Path(__file__).resolve().parents[1] / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Routers
    app.include_router(health.router, prefix="/v1")
    app.include_router(auth.router, prefix="/v1")
    app.include_router(users.router, prefix="/v1")
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
    app.include_router(websocket_router.router, prefix="/v1")

    return app


app = create_app()


