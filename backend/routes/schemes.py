"""Scholarship scheme catalog routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Scholarship
from backend.db.postgres import get_db
from backend.schemas import ScholarshipRead

router = APIRouter(prefix="/schemes", tags=["schemes"])


@router.get("", response_model=list[ScholarshipRead])
async def list_schemes(
    state: str | None = None,
    education_level: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[Scholarship]:
    stmt = select(Scholarship).order_by(Scholarship.deadline.is_(None), Scholarship.deadline).limit(limit)
    if state:
        stmt = stmt.where(Scholarship.state.in_([state, "All India"]))
    if education_level:
        stmt = stmt.where(Scholarship.education_levels.contains([education_level]))
    return list((await db.scalars(stmt)).all())


@router.get("/{scheme_id}", response_model=ScholarshipRead)
async def get_scheme(
    scheme_id: str,
    db: AsyncSession = Depends(get_db),
) -> Scholarship:
    scheme = await db.scalar(select(Scholarship).where(Scholarship.scheme_id == scheme_id))
    if scheme is None:
        raise HTTPException(status_code=404, detail="Scholarship not found")
    return scheme
