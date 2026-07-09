"""Universal Video Downloader - FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.api.middleware import SECURITY_HEADERS, limiter
from backend.api.routes import download, formats, history, info
from backend.api.routes import settings as settings_routes
from backend.config.logging_config import setup_logging
from backend.config.settings import get_settings
from backend.database.session import init_db
from backend.services.download_manager import download_manager
from backend.websocket.download_ws import router as ws_router

logger = logging.getLogger(__name__)
settings = get_settings()
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings)
    await init_db()
    await download_manager.start()
    logger.info(
        "Application started on port %s (version %s)",
        settings.backend_port,
        settings.app_version,
    )
    yield
    await download_manager.stop()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Modern universal video downloader powered by yt-dlp",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    for key, value in SECURITY_HEADERS.items():
        response.headers[key] = value
    return response


app.include_router(info.router)
app.include_router(download.router)
app.include_router(history.router)
app.include_router(settings_routes.router)
app.include_router(formats.router)
app.include_router(ws_router)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def serve_index():
    index = FRONTEND_DIR / "html" / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Universal Video Downloader API", "docs": "/docs"}


@app.get("/history")
async def serve_history():
    page = FRONTEND_DIR / "html" / "history.html"
    return FileResponse(page) if page.exists() else {"message": "History page not found"}


@app.get("/settings")
async def serve_settings_page():
    page = FRONTEND_DIR / "html" / "settings.html"
    return FileResponse(page) if page.exists() else {"message": "Settings page not found"}


@app.get("/robots.txt")
async def robots():
    robots_file = FRONTEND_DIR / "robots.txt"
    if robots_file.exists():
        return FileResponse(robots_file)
    return PlainTextResponse("User-agent: *\nAllow: /\n")


@app.get("/manifest.json")
async def manifest():
    manifest_file = FRONTEND_DIR / "manifest.json"
    return FileResponse(manifest_file) if manifest_file.exists() else {"name": settings.app_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.backend_port,
        reload=settings.debug,
    )
