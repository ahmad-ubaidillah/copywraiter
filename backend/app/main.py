from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.scheduler import scheduler_service
from config import settings
from database import close_db, init_db

# ── Logging setup ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# ── Lifespan ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup & shutdown lifecycle for the FastAPI application.

    Startup:
    1. Initialise database tables (dev mode; use Alembic in production).
    2. Start the APScheduler to automate copy generation.

    Shutdown:
    1. Gracefully stop the APScheduler.
    2. Dispose of the database engine connection pool.
    """
    logger.info("=== %s starting up ===", settings.APP_NAME)

    # ── Startup ────────────────────────────────────────────────────────────
    try:
        await init_db()
        logger.info("Database tables initialised")
    except Exception as exc:
        logger.warning("Database init skipped (may already exist or not needed): %s", exc)

    scheduler_service.start()
    logger.info("APScheduler started")

    yield  # ── Application runs here ──

    # ── Shutdown ───────────────────────────────────────────────────────────
    logger.info("=== %s shutting down ===", settings.APP_NAME)

    await scheduler_service.stop(wait=True)
    await close_db()
    logger.info("Cleanup complete")


# ── App factory ──────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description="Autonomous Research & Copywriting Agent",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Router mounting ──────────────────────────────────────────────────────────

# Import and mount routers below.
# Each router should be an APIRouter created via ``fastapi.APIRouter(prefix=...)``.
#
# Example:
#   from app.routers import users, drafts, trends, posts, agents, vault
#   app.include_router(users.router)
#   app.include_router(drafts.router)
#   app.include_router(trends.router)
#   app.include_router(posts.router)
#   app.include_router(agents.router)
#   app.include_router(vault.router)

# ── Static files ─────────────────────────────────────────────────────────────

# If you have a frontend build at <project>/web/public, serve it as static:
#   STATIC_DIR = settings.BASE_DIR.parent / "web" / "public"
#   if STATIC_DIR.is_dir():
#       app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")

# ── Health check ─────────────────────────────────────────────────────────────


@app.get("/api/status")
async def status() -> dict:
    """Simple health-check / status endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "ok",
        "scheduler_running": scheduler_service.running,
    }


@app.post("/api/scheduler/trigger")
async def trigger_scheduler() -> dict:
    """Manually trigger the automated pipeline once."""
    result = await scheduler_service.run_once_now()
    return {
        "status": "triggered",
        "result": result,
    }


@app.post("/api/scheduler/reschedule")
async def reschedule_scheduler() -> dict:
    """Reload the content calendar and reschedule all jobs."""
    scheduler_service.reschedule()
    return {
        "status": "rescheduled",
    }


# ── Direct execution ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
