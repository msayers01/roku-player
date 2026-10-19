"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from app.api import health, media, streaming
from app.config import Config
from app.database import Catalog
from app.errors import install_error_handlers


def create_app(config: Config, catalog: Catalog) -> FastAPI:
    app = FastAPI(title="Roku LAN Media", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.config = config
    app.state.catalog = catalog
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(media.router)
    app.include_router(streaming.router)
    return app
