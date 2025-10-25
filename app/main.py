from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import configure_logging, logger
from app.api.errors import register_exception_handlers
from app.api.v1.routers.books import router as books_router
from app.services.storage.json_store import JsonStore
from app.services.books import BooksService


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)

    app = FastAPI(title="JSON Book Service", version="0.1.0")

    # CORS
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    if "*" in origins:
        allow_origins = ["*"]
    else:
        allow_origins = origins or ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Services wiring
    store = JsonStore(settings.DATA_DIR, settings.DATA_FILE, settings.DATA_LOCK_FILE,
                      enable_backups=settings.ENABLE_BACKUPS,
                      backup_every_n_writes=settings.BACKUP_EVERY_N_WRITES)
    service = BooksService(store)
    app.state.books_service = service

    register_exception_handlers(app)

    @app.get("/healthz")
    async def healthz():
        info = await store.health()
        return JSONResponse({"status": "ok", **info})

    app.include_router(books_router, prefix="/api/v1")

    logger.info("Application started", extra={"event": "startup"})
    return app


app = create_app()
