"""AI Advisor chat routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth.security import get_current_user
from backend.config import settings
from backend.db.models import User
from backend.db.vector_store import hybrid_search
from backend.schemas import ChatRequest, ChatResponse, ChatSource

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Lazy-loaded FlashRank singleton
_ranker = None


def get_ranker():
    """Load FlashRank only when first needed."""
    global _ranker

    if _ranker is None:
        try:
            logger.info("Loading FlashRank Ranker...")
            from flashrank import Ranker

            _ranker = Ranker()
        except Exception:
            logger.exception("Failed to initialize FlashRank")
            _ranker = False

    return None if _ranker is False else _ranker


@router.post("", response_model=ChatResponse)
async def chat_advisor(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:

    message = payload.message.strip()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty",
        )

    filters = {}

    if current_user.category:
        filters["category"] = current_user.category

    if current_user.state:
        filters["state"] = current_user.state

    if current_user.education_level:
        filters["education_level"] = current_user.education_level

    try:
        search_results = hybrid_search(
            message,
            filters=filters,
            top_k=20,
        )
    except Exception:
        logger.exception("Hybrid search failed")
        search_results = []

    top_passages = []

    ranker = get_ranker()

    if search_results:

        if ranker:

            from flashrank import RerankRequest

            passages = [
                {
                    "id": i,
                    "text": r["text"],
                    "meta": {
                        "scheme_id": r["scheme_id"],
                        "scheme_name": r["scheme_name"],
                        "source_url": r["source_url"],
                    },
                }
                for i, r in enumerate(search_results)
            ]

            try:
                rerank_request = RerankRequest(
                    query=message,
                    passages=passages,
                )

                top_passages = ranker.rerank(rerank_request)[:5]

            except Exception:
                logger.exception("FlashRank failed")

        if not top_passages:
            top_passages = [
                {
                    "text": r["text"],
                    "meta": {
                        "scheme_id": r["scheme_id"],
                        "scheme_name": r["scheme_name"],
                        "source_url": r["source_url"],
                    },
                }
                for r in search_results[:5]
            ]

    sources = []

    seen = set()

    for passage in top_passages:

        meta = passage.get("meta", {})

        sid = meta.get("scheme_id")

        if sid and sid not in seen:

            seen.add(sid)

            sources.append(
                ChatSource(
                    scheme_id=sid,
                    scheme_name=meta.get("scheme_name") or sid,
                    source_url=meta.get("source_url") or "",
                )
            )

    answer = _generate_fallback_answer(top_passages)

    api_key = settings.GEMINI_API_KEY.strip()

    if api_key and top_passages:

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            context = "\n\n".join(
                [
                    f"""
Scheme: {p["meta"].get("scheme_name")}
ID: {p["meta"].get("scheme_id")}
Content:
{p["text"]}
"""
                    for p in top_passages
                ]
            )

            prompt = f"""
User State: {current_user.state}
Category: {current_user.category}
Education: {current_user.education_level}
Income: {current_user.income}

Scholarship Context:

{context}

Question:

{message}
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "Answer ONLY using the scholarship context."
                    )
                ),
            )

            if response.text:
                answer = response.text

        except Exception:
            logger.exception("Gemini failed")

    return ChatResponse(
        answer=answer,
        sources=sources,
    )


def _generate_fallback_answer(
    passages: list[dict[str, Any]],
) -> str:

    if not passages:
        return (
            "I couldn't find any relevant scholarships matching your query."
        )

    text = "Here are the most relevant scholarship matches:\n\n"

    for i, p in enumerate(passages, start=1):

        meta = p.get("meta", {})

        name = meta.get("scheme_name", "Scholarship")

        sid = meta.get("scheme_id", "")

        snippet = p["text"][:200]

        text += (
            f"{i}. **[{name}](/scheme/{sid})**\n"
            f"{snippet}...\n\n"
        )

    return text
