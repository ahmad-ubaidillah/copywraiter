from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base, get_db
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="copywrAIter API",
    version="1.5",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/")
async def root():
    return {"message": "copywrAIter API", "version": "1.5"}


@app.get("/health")
async def health():
    return {"status": "ok"}
