"""Dashboard aggregation route."""

from __future__ import annotations

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


@router.get("", response_model=DashboardRead)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardRead:
    scholarships = list((await db.scalars(select(Scholarship))).all())
    top_matches = rank_scholarships(current_user, scholarships, limit=5)

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

    return DashboardRead(
        name=_display_name(current_user.email),
        profile_completion=profile_completion(current_user),
        top_matches=top_matches,
        saved_scholarships=saved_items,
    )


def _display_name(email: str) -> str:
    return email.split("@", 1)[0].replace(".", " ").replace("_", " ").title()
