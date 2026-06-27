"""AI Advisor chat routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from flashrank import Ranker, RerankRequest

from backend.auth.security import get_current_user
from backend.config import settings
from backend.db.models import User
from backend.db.vector_store import hybrid_search
from backend.schemas import ChatRequest, ChatResponse, ChatSource

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize FlashRank ranker (singleton)
try:
    logger.info("Initializing FlashRank Ranker...")
    _ranker = Ranker()
except Exception as e:
    logger.exception("Failed to initialize FlashRank Ranker")
    _ranker = None


@router.post("", response_model=ChatResponse)
async def chat_advisor(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """RAG-based chat advisor endpoint."""
    message = payload.message.strip()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty",
        )

    # 1. Build eligibility filters based on user profile
    filters = {}
    if current_user.category:
        filters["category"] = current_user.category
    if current_user.state:
        filters["state"] = current_user.state
    if current_user.education_level:
        filters["education_level"] = current_user.education_level

    # 2. Run hybrid search
    try:
        search_results = hybrid_search(message, filters=filters, top_k=20)
    except Exception as e:
        logger.exception("Error during hybrid search")
        search_results = []

    # 3. Rerank using FlashRank
    top_passages = []
    if search_results:
        if _ranker is not None:
            passages = [
                {
                    "id": idx,
                    "text": result["text"],
                    "meta": {
                        "scheme_id": result["scheme_id"],
                        "scheme_name": result["scheme_name"],
                        "source_url": result["source_url"],
                    },
                }
                for idx, result in enumerate(search_results)
            ]
            try:
                rerank_req = RerankRequest(query=message, passages=passages)
                reranked = _ranker.rerank(rerank_req)
                top_passages = reranked[:5]
            except Exception as e:
                logger.exception("Error during reranking, falling back to top search results")
                top_passages = [
                    {
                        "text": res["text"],
                        "meta": {
                            "scheme_id": res["scheme_id"],
                            "scheme_name": res["scheme_name"],
                            "source_url": res["source_url"],
                        },
                    }
                    for res in search_results[:5]
                ]
        else:
            top_passages = [
                {
                    "text": res["text"],
                    "meta": {
                        "scheme_id": res["scheme_id"],
                        "scheme_name": res["scheme_name"],
                        "source_url": res["source_url"],
                    },
                }
                for res in search_results[:5]
            ]

    # 4. Extract unique source metadata
    sources: list[ChatSource] = []
    seen_scheme_ids = set()
    for passage in top_passages:
        meta = passage.get("meta", {})
        scheme_id = meta.get("scheme_id")
        if scheme_id and scheme_id not in seen_scheme_ids:
            seen_scheme_ids.add(scheme_id)
            sources.append(
                ChatSource(
                    scheme_id=scheme_id,
                    scheme_name=meta.get("scheme_name") or scheme_id,
                    source_url=meta.get("source_url") or "",
                )
            )

    # 5. Generate response (Gemini or Fallback)
    api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""
    if api_key and top_passages:
        try:
            from google import genai
            # pyrefly: ignore [missing-import]
            from google.genai import types

            client = genai.Client(api_key=api_key)

            # Construct grounding context
            context_parts = []
            for idx, p in enumerate(top_passages):
                meta = p.get("meta", {})
                context_parts.append(
                    f"Source: {meta.get('scheme_name')} (ID: {meta.get('scheme_id')})\n"
                    f"Content: {p.get('text')}\n"
                    f"Source URL: {meta.get('source_url')}\n"
                )
            context_text = "\n---\n".join(context_parts)

            system_instruction = (
                "You are a helpful, professional AI Scholarship Advisor. "
                "Your goal is to guide students to find relevant scholarships based on their question and the retrieved context. "
                "Use only the provided context to answer the question. If the context does not contain enough information to answer, "
                "politely say that you don't have that information. Do not make up facts or external links.\n\n"
                "When referencing any scholarship scheme, you MUST link it using markdown syntax: [Scheme Name](/scheme/scheme_id) "
                "where Scheme Name is the name of the scholarship and scheme_id is the exact scheme_id from the context metadata. "
                "Do not invent URLs; only use the specified '/scheme/scheme_id' path format."
            )

            prompt = (
                f"User Profile details:\n"
                f"- State: {current_user.state or 'Not specified'}\n"
                f"- Category: {current_user.category or 'Not specified'}\n"
                f"- Education Level: {current_user.education_level or 'Not specified'}\n"
                f"- Family Income: {current_user.income or 'Not specified'}\n\n"
                f"Retrieved Scholarship Information:\n"
                f"{context_text}\n\n"
                f"User Question: {message}\n"
                f"Response:"
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                ),
            )
            answer = response.text
        except Exception as e:
            logger.exception("Gemini execution failed, using fallback summary")
            answer = _generate_fallback_answer(top_passages)
    else:
        answer = _generate_fallback_answer(top_passages)

    return ChatResponse(answer=answer, sources=sources)


def _generate_fallback_answer(top_passages: list[dict[str, Any]]) -> str:
    if not top_passages:
        return "I couldn't find any relevant scholarships matching your query in our database."

    ans = (
        "Hello! I am currently running in local retrieval-only mode. "
        "However, based on your profile and query, I retrieved the following matching scholarship schemes:\n\n"
    )
    for idx, p in enumerate(top_passages):
        meta = p.get("meta", {})
        name = meta.get("scheme_name") or meta.get("scheme_id") or "Scholarship"
        sid = meta.get("scheme_id") or ""
        text = p.get("text", "")
        # Get snippet
        snippet = text[:200] + "..." if len(text) > 200 else text
        ans += f"{idx + 1}. **[{name}](/scheme/{sid})**\n   *Match Excerpt:* \"{snippet}\"\n\n"

    ans += "You can click on the links above to view full details and apply!"
    return ans
