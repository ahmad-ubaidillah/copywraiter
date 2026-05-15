from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.workflow import get_content_workflow
from app.database import get_db

router = APIRouter(prefix="/api/workflow", tags=["Workflow"])


class RunRequest(BaseModel):
    topic: str
    language: str = "en"
    user_id: str | None = None


class VariationsRequest(BaseModel):
    topic: str
    language: str = "en"
    user_id: str | None = None


@router.post("/run")
async def run_workflow(req: RunRequest, db: Session = Depends(get_db)) -> Any:
    wf = get_content_workflow(get_session=lambda: db)
    return wf.run(topic=req.topic, language=req.language, user_id=req.user_id)


@router.post("/variations")
async def run_variations(req: VariationsRequest, db: Session = Depends(get_db)) -> Any:
    wf = get_content_workflow(get_session=lambda: db)
    return wf.run_with_variations(topic=req.topic, language=req.language, user_id=req.user_id)


@router.get("/log")
async def get_log() -> Any:
    wf = get_content_workflow()
    return {"log": wf.get_log()}
