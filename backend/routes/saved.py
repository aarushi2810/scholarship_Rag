"""Saved scholarship routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.auth.security import get_current_user
from backend.db.models import SavedScholarship, Scholarship, User
from backend.db.postgres import get_db
from backend.recommendation.eligibility_scorer import days_until_deadline
from backend.schemas import SavedScholarshipRead

router = APIRouter(prefix="/saved", tags=["saved scholarships"])


def _saved_response(saved: SavedScholarship) -> SavedScholarshipRead:
    return SavedScholarshipRead(
        id=saved.id,
        saved_at=saved.saved_at,
        scholarship=saved.scholarship,
        deadline_days_left=days_until_deadline(saved.scholarship.deadline),
    )


@router.get("", response_model=list[SavedScholarshipRead])
async def list_saved(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SavedScholarshipRead]:
    stmt = (
        select(SavedScholarship)
        .where(SavedScholarship.user_id == current_user.id)
        .options(selectinload(SavedScholarship.scholarship))
        .order_by(SavedScholarship.saved_at.desc())
    )
    saved = list((await db.scalars(stmt)).all())
    return [_saved_response(item) for item in saved]


@router.post("/{scheme_id}", response_model=SavedScholarshipRead, status_code=status.HTTP_201_CREATED)
async def save_scholarship(
    scheme_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedScholarshipRead:
    scholarship = await db.scalar(select(Scholarship).where(Scholarship.scheme_id == scheme_id))
    if scholarship is None:
        raise HTTPException(status_code=404, detail="Scholarship not found")

    existing_stmt = (
        select(SavedScholarship)
        .where(SavedScholarship.user_id == current_user.id)
        .where(SavedScholarship.scholarship_id == scholarship.id)
        .options(selectinload(SavedScholarship.scholarship))
    )
    existing = await db.scalar(existing_stmt)
    if existing:
        return _saved_response(existing)

    saved = SavedScholarship(user_id=current_user.id, scholarship_id=scholarship.id)
    db.add(saved)
    await db.commit()
    await db.refresh(saved)
    saved.scholarship = scholarship
    return _saved_response(saved)


@router.delete("/{scheme_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def unsave_scholarship(
    scheme_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    scholarship = await db.scalar(select(Scholarship).where(Scholarship.scheme_id == scheme_id))
    if scholarship is None:
        raise HTTPException(status_code=404, detail="Scholarship not found")

    saved = await db.scalar(
        select(SavedScholarship)
        .where(SavedScholarship.user_id == current_user.id)
        .where(SavedScholarship.scholarship_id == scholarship.id)
    )
    if saved is not None:
        await db.delete(saved)
        await db.commit()
