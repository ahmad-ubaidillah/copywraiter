from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import (
    agent,
    drafts,
    posts,
    trends,
    niches,
    vault,
    repliz,
    linkedin,
    profile,
    settings,
    style_references,
    style,
    workflow,
    research,
    config,
    calendar,
    publish,
    agent_log,
    topics,
    template,
    platforms,
)
from app.scheduler import scheduler_service
from config import settings as app_settings

# ── Logging setup ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if app_settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# ── Lifespan ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("=== %s starting up ===", app_settings.APP_NAME)

    # ── Startup ──────────────────────────────────────────────────────────
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialised")
    except Exception as exc:
        logger.warning("Database init skipped (may already exist or not needed): %s", exc)

    try:
        scheduler_service.start()
        logger.info("APScheduler started")
    except Exception as exc:
        logger.warning("Scheduler start skipped: %s", exc)

    yield  # ── Application runs here ──

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("=== %s shutting down ===", app_settings.APP_NAME)

    try:
        await scheduler_service.stop(wait=True)
    except Exception as exc:
        logger.warning("Scheduler stop error: %s", exc)

    engine.dispose()
    logger.info("Cleanup complete")


# ── App factory ──────────────────────────────────────────────────────────────

app = FastAPI(
    title=app_settings.APP_NAME,
    description="Autonomous Research & Copywriting Agent",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Router mounting ──────────────────────────────────────────────────────────

# Core CRUD routers
app.include_router(agent.router)
app.include_router(drafts.router)
app.include_router(posts.router)
app.include_router(trends.router)
app.include_router(niches.router)
app.include_router(vault.router)
app.include_router(repliz.router)
app.include_router(linkedin.router)
app.include_router(profile.router)
app.include_router(settings.router)
app.include_router(style_references.router)

# PRD v1.5 feature routers
app.include_router(style.router)
app.include_router(workflow.router)
app.include_router(research.router)
app.include_router(config.router)
app.include_router(calendar.router)
app.include_router(publish.router)
app.include_router(agent_log.router)
app.include_router(topics.router)
app.include_router(template.router)
app.include_router(platforms.router)

# ── Base endpoints ───────────────────────────────────────────────────────────


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "copywrAIter API",
        "version": "1.0.0",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/status")
async def status() -> dict[str, Any]:
    return {
        "app": app_settings.APP_NAME,
        "version": "1.0.0",
        "status": "ok",
        "scheduler_running": scheduler_service.running,
    }


@app.post("/api/scheduler/trigger")
async def trigger_scheduler() -> dict[str, Any]:
    result = await scheduler_service.run_once_now()
    return {
        "status": "triggered",
        "result": result,
    }


@app.post("/api/scheduler/reschedule")
async def reschedule_scheduler() -> dict[str, Any]:
    scheduler_service.reschedule()
    return {
        "status": "rescheduled",
    }
