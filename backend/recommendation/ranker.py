"""Rank scholarships for a user profile."""

from __future__ import annotations

from backend.db.models import Scholarship, User
from backend.recommendation.eligibility_scorer import score_scholarship


def rank_scholarships(
    user: User,
    scholarships: list[Scholarship],
    *,
    limit: int = 5,
    include_ineligible: bool = False,
) -> list[dict]:
    scored = [score_scholarship(user, scholarship) for scholarship in scholarships]
    if not include_ineligible:
        scored = [item for item in scored if item["match_score"] > 0]

    return sorted(
        scored,
        key=lambda item: (
            item["match_score"],
            _deadline_sort_value(item["deadline_days_left"]),
        ),
        reverse=True,
    )[:limit]


def _deadline_sort_value(days_left: int | None) -> int:
    if days_left is None or days_left < 0:
        return -1
    return max(0, 365 - days_left)
