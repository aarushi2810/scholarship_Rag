"""FastAPI app for ScholarMatch AI."""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from backend.auth.routes import router as auth_router
from backend.db.models import EligibilityRule, Scholarship
from backend.db.postgres import AsyncSessionLocal, init_db
from backend.routes.chat import router as chat_router
from backend.routes.dashboard import router as dashboard_router
from backend.routes.profile import router as profile_router
from backend.routes.recommendations import router as recommendations_router
from backend.routes.saved import router as saved_router
from backend.routes.schemes import router as schemes_router
from backend.routes.search import router as search_router

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_schemes.json"

app = FastAPI(title="ScholarMatch AI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _auto_seed() -> None:
    """Seed the scholarships table from sample_schemes.json if it is empty.

    This is intentionally idempotent: if even one scholarship row exists the
    function returns immediately, so redeployments are safe.
    """
    if not DATA_PATH.exists():
        logger.warning("seed: %s not found, skipping auto-seed", DATA_PATH)
        return

    async with AsyncSessionLocal() as db:
        count = await db.scalar(select(func.count()).select_from(Scholarship))
        if count and count > 0:
            logger.info("seed: scholarships table already has %d rows — skipping", count)
            return

        logger.info("seed: scholarships table is empty — seeding from %s", DATA_PATH)
        schemes = json.loads(DATA_PATH.read_text())

        for item in schemes:
            deadline = date.fromisoformat(item["deadline"]) if item.get("deadline") else None
            scholarship = Scholarship(
                scheme_id=item["scheme_id"],
                scheme_name=item["scheme_name"],
                provider=item["provider"],
                categories=item["categories"],
                income_ceiling=item["income_ceiling"],
                education_levels=item["education_levels"],
                state=item["state"],
                benefits=item["benefits"],
                deadline=deadline,
                eligibility_text=item["eligibility_text"],
                documents_required=item["documents_required"],
                application_process=item["application_process"],
                source_url=item["source_url"],
            )
            db.add(scholarship)

        await db.flush()  # get scholarship IDs before adding rules

        # Rebuild eligibility rules
        scholarships_in_db = list((await db.scalars(select(Scholarship))).all())
        for s in scholarships_in_db:
            for category in s.categories or []:
                db.add(EligibilityRule(scholarship_id=s.id, rule_type="category", rule_value=category))
            for level in s.education_levels or []:
                db.add(EligibilityRule(scholarship_id=s.id, rule_type="education_level", rule_value=level))
            if s.income_ceiling is not None:
                db.add(EligibilityRule(scholarship_id=s.id, rule_type="income_ceiling", rule_value=str(s.income_ceiling)))
            db.add(EligibilityRule(scholarship_id=s.id, rule_type="state", rule_value=s.state))

        await db.commit()
        logger.info("seed: inserted %d scholarships successfully", len(schemes))


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()
    await _auto_seed()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(schemes_router)
app.include_router(recommendations_router)
app.include_router(saved_router)
app.include_router(dashboard_router)
app.include_router(chat_router)
app.include_router(search_router)
