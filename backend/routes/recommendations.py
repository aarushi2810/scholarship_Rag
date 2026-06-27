"""Recommendation routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.security import get_current_user
from backend.db.models import Scholarship, User
from backend.db.postgres import get_db
from backend.recommendation.ranker import rank_scholarships
from backend.schemas import RecommendationRead

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendationRead])
async def get_recommendations(
    limit: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    scholarships = list((await db.scalars(select(Scholarship))).all())
    return rank_scholarships(current_user, scholarships, limit=limit)
