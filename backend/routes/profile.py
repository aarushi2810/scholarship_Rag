"""Profile routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.security import get_current_user
from backend.db.models import User
from backend.db.postgres import get_db
from backend.recommendation.eligibility_scorer import profile_completion
from backend.routes.dashboard import invalidate_dashboard_cache
from backend.schemas import ProfileUpdate, UserProfile

router = APIRouter(prefix="/profile", tags=["profile"])


def _profile_response(user: User) -> UserProfile:
    return UserProfile(
        id=user.id,
        email=user.email,
        category=user.category,
        income=user.income,
        education_level=user.education_level,
        state=user.state,
        degree=user.degree,
        cgpa=user.cgpa,
        gender=user.gender,
        profile_completion=profile_completion(user),
    )


@router.get("", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)) -> UserProfile:
    return _profile_response(current_user)


@router.put("", response_model=UserProfile)
async def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(current_user, field, value)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    # Profile changed — bust the per-user dashboard cache so next load is fresh
    invalidate_dashboard_cache(current_user.id)
    return _profile_response(current_user)
