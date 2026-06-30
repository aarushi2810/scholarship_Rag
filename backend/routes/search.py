"""Semantic search route — auth-optional hybrid dense+sparse search with result caching."""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from typing import Literal

from cachetools import TTLCache
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.security import get_optional_user
from backend.db.models import Scholarship, User
from backend.db.postgres import get_db
from backend.db.vector_store import hybrid_search
from backend.recommendation.eligibility_scorer import (
    days_until_deadline,
    score_scholarship,
)
from backend.schemas import SearchResult, ScholarshipRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

# ── Search result cache ────────────────────────────────────────────────────────
# Anonymous results: 5 min TTL (stable, no profile dependency)
# Authenticated results: 2 min TTL (personalised match scores vary with profile)
# maxsize=200 keeps memory bounded; LRU eviction discards cold queries first.
_anon_cache: TTLCache = TTLCache(maxsize=200, ttl=300)
_auth_cache: TTLCache = TTLCache(maxsize=200, ttl=120)
_search_lock = threading.Lock()


def _cache_key(q: str, state: str, category: str, education_level: str, sort: str, limit: int, user_id: int | None) -> str:
    """Stable hash key for a search parameter combination."""
    raw = json.dumps(
        {"q": q, "state": state, "category": category, "edu": education_level, "sort": sort, "limit": limit, "uid": user_id},
        sort_keys=True,
    )
    return hashlib.md5(raw.encode()).hexdigest()  # noqa: S324 — not used for security


def _get_search_cache(user_id: int | None) -> TTLCache:
    return _auth_cache if user_id is not None else _anon_cache


@router.get("", response_model=list[SearchResult])
async def semantic_search(
    q: str = Query(default="", description="Free-text semantic query"),
    state: str = Query(default="", description="Filter by state"),
    category: str = Query(default="", description="Filter by category"),
    education_level: str = Query(default="", description="Filter by education level"),
    sort: Literal["match", "deadline"] = Query(default="match"),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> list[SearchResult]:
    """Hybrid semantic search over scholarships.

    - Authenticated users: results include personalised match_score, reasons, and
      missing_or_mismatch based on their profile.
    - Anonymous users: match_score is None, reasons/missing are empty.
    - Results are cached per unique (query, filters, user_id) combination.
    """
    query_text = q.strip()
    user_id = current_user.id if current_user is not None else None

    # ── Cache lookup ──────────────────────────────────────────────────────────
    key = _cache_key(query_text, state, category, education_level, sort, limit, user_id)
    cache = _get_search_cache(user_id)
    with _search_lock:
        cached = cache.get(key)
    if cached is not None:
        logger.debug("Search cache hit: %s", key)
        return cached

    # ── Build filters for Qdrant ───────────────────────────────────────────────
    filters: dict = {}
    if state:
        filters["state"] = state
    if category:
        filters["category"] = category
    if education_level:
        filters["education_level"] = education_level

    # ── Run hybrid search — fall back to browsing all if no query ─────────────
    try:
        if query_text:
            raw_results = hybrid_search(query_text, filters=filters, top_k=limit * 2)
        else:
            raw_results = []
    except Exception:
        logger.exception("Hybrid search failed, falling back to Postgres scan")
        raw_results = []

    # ── Collect unique scheme_ids (preserving semantic rank order) ────────────
    seen_ids: list[str] = []
    score_map: dict[str, float] = {}
    for result in raw_results:
        sid = result.get("scheme_id")
        if sid and sid not in score_map:
            seen_ids.append(sid)
            score_map[sid] = float(result.get("score", 0.0))

    # ── If no semantic results (empty query or search failed), do a DB scan ───
    if not seen_ids:
        stmt = select(Scholarship)
        scholarships = list((await db.scalars(stmt)).all())
        if state:
            scholarships = [
                s for s in scholarships
                if s.state.casefold() == state.casefold() or s.state.casefold() == "all india"
            ]
        if category:
            scholarships = [
                s for s in scholarships
                if any(c.casefold() == category.casefold() for c in (s.categories or []))
            ]
        if education_level:
            scholarships = [
                s for s in scholarships
                if any(e.casefold() == education_level.casefold() for e in (s.education_levels or []))
            ]
        scheme_map = {s.scheme_id: s for s in scholarships}
        seen_ids = list(scheme_map.keys())
        score_map = {sid: 0.0 for sid in seen_ids}
    else:
        # Fetch the full Scholarship rows for the matched scheme_ids only
        stmt = select(Scholarship).where(Scholarship.scheme_id.in_(seen_ids))
        rows = list((await db.scalars(stmt)).all())
        scheme_map = {s.scheme_id: s for s in rows}

    # ── Build response list in semantic rank order ────────────────────────────
    output: list[SearchResult] = []
    for sid in seen_ids:
        scholarship = scheme_map.get(sid)
        if scholarship is None:
            continue

        semantic_score = score_map.get(sid, 0.0)
        ddl = days_until_deadline(scholarship.deadline)

        if current_user is not None:
            scored = score_scholarship(current_user, scholarship)
            match_score: int | None = scored["match_score"]
            reasons = scored["reasons"]
            missing_or_mismatch = scored["missing_or_mismatch"]
        else:
            match_score = None
            reasons = []
            missing_or_mismatch = []

        output.append(
            SearchResult(
                scholarship=ScholarshipRead.model_validate(scholarship),
                match_score=match_score,
                semantic_score=semantic_score,
                deadline_days_left=ddl,
                reasons=reasons,
                missing_or_mismatch=missing_or_mismatch,
            )
        )

    # ── Secondary sort ────────────────────────────────────────────────────────
    if sort == "deadline":
        output.sort(
            key=lambda r: (
                r.deadline_days_left if r.deadline_days_left is not None else 9999
            )
        )
    elif sort == "match" and current_user is not None:
        output.sort(key=lambda r: (r.match_score or 0), reverse=True)

    result_slice = output[:limit]

    # ── Store in cache ────────────────────────────────────────────────────────
    with _search_lock:
        cache[key] = result_slice

    return result_slice
