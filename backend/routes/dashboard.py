"""Dashboard aggregation route — with per-user TTL cache."""

from __future__ import annotations

import threading
from functools import lru_cache

from cachetools import TTLCache
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.auth.security import get_current_user
from backend.db.models import SavedScholarship, Scholarship, User
from backend.db.postgres import get_db
from backend.recommendation.eligibility_scorer import days_until_deadline, profile_completion
from backend.recommendation.ranker import rank_scholarships
from backend.schemas import DashboardRead, SavedScholarshipRead

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# ── Per-user in-process cache ──────────────────────────────────────────────────
# TTL=60s: dashboard data refreshes within a minute, feels instant on re-visit.
# maxsize=500: accommodates up to 500 concurrent users before LRU eviction.
_dashboard_cache: TTLCache = TTLCache(maxsize=500, ttl=60)
_cache_lock = threading.Lock()


def _get_cached(user_id: int):
    with _cache_lock:
        return _dashboard_cache.get(user_id)


def _set_cached(user_id: int, value: DashboardRead) -> None:
    with _cache_lock:
        _dashboard_cache[user_id] = value


def invalidate_dashboard_cache(user_id: int) -> None:
    """Call this whenever a user's profile or saved scholarships change."""
    with _cache_lock:
        _dashboard_cache.pop(user_id, None)


@router.get("", response_model=DashboardRead)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardRead:
    # ── Cache hit ──────────────────────────────────────────────────────────────
    cached = _get_cached(current_user.id)
    if cached is not None:
        return cached

    # ── Single scholarship fetch shared by both top_matches and eligible_count ─
    scholarships = list((await db.scalars(select(Scholarship))).all())
    eligible_count = len(scholarships)

    top_matches = rank_scholarships(current_user, scholarships, limit=5)

    # ── Saved scholarships ─────────────────────────────────────────────────────
    saved_stmt = (
        select(SavedScholarship)
        .where(SavedScholarship.user_id == current_user.id)
        .options(selectinload(SavedScholarship.scholarship))
        .order_by(SavedScholarship.saved_at.desc())
    )
    saved = list((await db.scalars(saved_stmt)).all())
    saved_items = [
        SavedScholarshipRead(
            id=item.id,
            saved_at=item.saved_at,
            scholarship=item.scholarship,
            deadline_days_left=days_until_deadline(item.scholarship.deadline),
        )
        for item in saved
    ]

    result = DashboardRead(
        name=_display_name(current_user.email),
        profile_completion=profile_completion(current_user),
        top_matches=top_matches,
        saved_scholarships=saved_items,
        eligible_count=eligible_count,
        category=current_user.category,
        income=current_user.income,
        education_level=current_user.education_level,
        state=current_user.state,
        degree=current_user.degree,
        cgpa=current_user.cgpa,
        gender=current_user.gender,
    )

    _set_cached(current_user.id, result)
    return result


def _display_name(email: str) -> str:
    return email.split("@", 1)[0].replace(".", " ").replace("_", " ").title()
