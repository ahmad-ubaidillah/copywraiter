from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.agents.copywriter import CopywriterAgent, _load_content_calendar, copywriter_agent
from app.models import Post, Trend as TrendModel
from config import settings

logger = logging.getLogger(__name__)

CONTENT_CALENDAR_PATH = settings.BASE_DIR.parent / "knowledge_base" / "content_calendar.json"

JobFunc = Callable[[], Any]


class SchedulerService:

    def __init__(
        self,
        agent: CopywriterAgent | None = None,
        get_session: Callable[[], Any] | None = None,
    ) -> None:
        self._scheduler = AsyncIOScheduler(timezone="Asia/Jakarta")
        self._agent = agent or copywriter_agent
        self._get_session = get_session
        self._job_ids: list[str] = []

    @property
    def scheduler(self) -> AsyncIOScheduler:
        return self._scheduler

    @property
    def running(self) -> bool:
        return self._scheduler.running

    def start(self) -> None:
        if self._scheduler.running:
            logger.warning("Scheduler is already running — skipping start")
            return

        calendar = _load_content_calendar()
        if not calendar:
            logger.warning("Content calendar is empty — scheduler will not schedule jobs")
            self._scheduler.start()
            return

        self._schedule_generation_jobs(calendar)
        self._schedule_maintenance_jobs()

        self._scheduler.start()
        logger.info(
            "Scheduler started with %d jobs | timezone=%s",
            len(self._job_ids),
            self._scheduler.timezone,
        )

    async def stop(self, wait: bool = True) -> None:
        if not self._scheduler.running:
            return
        self._scheduler.shutdown(wait=wait)
        logger.info("Scheduler stopped")

    def reschedule(self) -> None:
        self._remove_all_jobs()
        calendar = _load_content_calendar()
        if calendar:
            self._schedule_generation_jobs(calendar)
            self._schedule_maintenance_jobs()
        logger.info("Scheduler rescheduled with %d jobs", len(self._job_ids))

    async def run_once_now(self) -> dict[str, Any]:
        return await self._pipeline()

    def _schedule_generation_jobs(self, calendar: dict[str, Any]) -> None:
        schedule = calendar.get("schedule", {})
        preferred_hours = schedule.get("preferred_hours", ["07:00", "19:00"])
        posting_days = calendar.get("posting_days", ["monday", "tuesday", "wednesday", "thursday", "friday"])
        weekend_posting = calendar.get("weekend_posting", False)

        day_map = {
            "monday": "mon",
            "tuesday": "tue",
            "wednesday": "wed",
            "thursday": "thu",
            "friday": "fri",
            "saturday": "sat",
            "sunday": "sun",
        }

        dow_parts: list[str] = []
        for day in posting_days:
            abbr = day_map.get(day.lower())
            if abbr:
                dow_parts.append(abbr)
        if weekend_posting:
            for day in ("saturday", "sunday"):
                abbr = day_map.get(day)
                if abbr and abbr not in dow_parts:
                    dow_parts.append(abbr)

        if not dow_parts:
            dow_parts = ["mon", "tue", "wed", "thu", "fri"]

        dow_expr = ",".join(dow_parts)

        for hour_str in preferred_hours:
            try:
                parsed = time.fromisoformat(hour_str)
            except ValueError:
                logger.warning("Invalid preferred_hour '%s' — skipping", hour_str)
                continue

            job_id = f"generate_copy_{hour_str.replace(':', '')}"
            self._scheduler.add_job(
                self._pipeline,
                CronTrigger(
                    day_of_week=dow_expr,
                    hour=parsed.hour,
                    minute=parsed.minute,
                    timezone="Asia/Jakarta",
                ),
                id=job_id,
                replace_existing=True,
                name=f"Generate copy @ {hour_str}",
            )
            self._job_ids.append(job_id)
            logger.debug("Scheduled job '%s' at %s on [%s]", job_id, hour_str, dow_expr)

    def _schedule_maintenance_jobs(self) -> None:
        cleanup_id = "cleanup_stale_posts"
        self._scheduler.add_job(
            self._cleanup_stale_posts,
            CronTrigger(hour=3, minute=0, timezone="Asia/Jakarta"),
            id=cleanup_id,
            replace_existing=True,
            name="Cleanup stale posts (daily @ 03:00 WIB)",
        )
        self._job_ids.append(cleanup_id)

    def _remove_all_jobs(self) -> None:
        for job_id in self._job_ids:
            try:
                self._scheduler.remove_job(job_id)
            except Exception:
                pass
        self._job_ids.clear()

    async def _pipeline(self) -> dict[str, Any]:
        logger.info("Scheduler pipeline: starting automated copy generation")

        result: dict[str, Any] = {
            "status": "ok",
            "generated": [],
            "errors": [],
        }

        if self._get_session is None:
            logger.warning("No DB session factory configured — skipping persistence")
            result["status"] = "no_session"
            return result

        db: Session = self._get_session()
        try:
            trend = self._pick_best_trend(db)

            if trend is None:
                logger.info("No trends available — generating with generic topic")
                topic = self._pick_fallback_topic()
            else:
                topic = trend.keyword

            try:
                gen_result = await self._agent.generate(
                    topic,
                    platform="linkedin",
                    trend_id=trend.id if trend else None,
                    db_session=db,
                )
                result["generated"].append(gen_result)
                logger.info("Pipeline: generated copy for '%s' (%d chars)", topic, gen_result["chars"])
            except Exception as exc:
                logger.exception("Pipeline: generation failed for '%s'", topic)
                result["errors"].append({"topic": topic, "error": str(exc)})

            db.commit()
        finally:
            db.close()

        return result

    def _pick_best_trend(self, db: Session) -> Any | None:
        return db.query(TrendModel).order_by(desc(TrendModel.score)).first()

    def _pick_fallback_topic(self) -> str:
        return "AI dan masa depan pekerjaan di Indonesia"

    async def _cleanup_stale_posts(self) -> None:
        if self._get_session is None:
            return
        db: Session = self._get_session()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            stale = (
                db.query(Post)
                .filter(Post.status == "scheduled")
                .filter(Post.created_at < cutoff)
                .all()
            )
            for post in stale:
                post.status = "archived"
                logger.info("Archived stale scheduled post %s", post.id)
            db.commit()
            if stale:
                logger.info("Cleanup: archived %d stale posts", len(stale))
        finally:
            db.close()


scheduler_service = SchedulerService()
