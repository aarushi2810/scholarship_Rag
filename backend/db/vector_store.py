"""
Qdrant hybrid (dense + sparse) vector store for ScholarshipRAG.

Uses:
  - Dense embeddings via sentence-transformers (BAAI/bge-small-en-v1.5, dim=384)
  - Sparse embeddings via scikit-learn TfidfVectorizer (IDF-weighted)
  - Reciprocal Rank Fusion (RRF) to merge both retrieval signals

The TfidfVectorizer is lazily loaded from the real indexed corpus. Run
``python -m ingestion.index_data`` before using hybrid search so sparse
retrieval is trained on scholarship text, not a placeholder corpus.
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any

import numpy as np
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

from backend.config import settings

logger = logging.getLogger(__name__)

# ── Paths ───────────────────────────────────────────────────────────────────────

_VECTORIZER_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "tfidf_vectorizer.pkl"

# ── Clients / models (module-level singletons) ─────────────────────────────────

qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

_dense_model: SentenceTransformer | None = None
_tfidf_vectorizer: TfidfVectorizer | None = None


def _get_dense_model() -> SentenceTransformer:
    """Lazy-load the dense embedding model."""
    global _dense_model
    if _dense_model is None:
        logger.info("Loading dense embedding model: %s", settings.EMBEDDING_MODEL)
        _dense_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _dense_model


def _get_tfidf_vectorizer() -> TfidfVectorizer:
    """Lazy-load the real-corpus TF-IDF vectorizer.

    If a pre-fitted pickle exists at ``_VECTORIZER_PATH`` it is loaded directly.
    Otherwise the caller must run ingestion first. This intentionally avoids a
    fake "hybrid" setup where sparse retrieval is fitted on generic sentences.
    """
    global _tfidf_vectorizer
    if _tfidf_vectorizer is not None:
        return _tfidf_vectorizer

    if _VECTORIZER_PATH.exists():
        logger.info("Loading TF-IDF vectorizer from %s", _VECTORIZER_PATH)
        with open(_VECTORIZER_PATH, "rb") as fh:
            _tfidf_vectorizer = pickle.load(fh)  # noqa: S301
        return _tfidf_vectorizer

    raise RuntimeError(
        "No fitted TF-IDF vectorizer found. Run `python -m ingestion.index_data` "
        "so sparse retrieval is trained on the real scholarship corpus."
    )


# ── Embedding helpers ───────────────────────────────────────────────────────────


def get_dense_embedding(text: str) -> list[float]:
    """Return a normalised dense embedding vector for *text*."""
    model = _get_dense_model()
    embedding: np.ndarray = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def get_sparse_embedding(text: str) -> dict[str, list]:
    """Return a sparse embedding dict ``{indices: [...], values: [...]}`` for *text*."""
    vectorizer = _get_tfidf_vectorizer()
    sparse_matrix = vectorizer.transform([text])
    coo = sparse_matrix.tocoo()
    return {
        "indices": coo.col.tolist(),
        "values": coo.data.tolist(),
    }


# ── Hybrid search ──────────────────────────────────────────────────────────────


def _build_qdrant_filter(filters: dict[str, Any] | None) -> models.Filter | None:
    """Translate caller-supplied metadata filters into a Qdrant ``Filter``."""
    if not filters:
        return None

    conditions: list[models.FieldCondition] = []

    if filters.get("category"):
        val = filters["category"]
        conditions.append(
            models.FieldCondition(
                key="categories",
                match=models.MatchAny(
                    any=val if isinstance(val, list) else [val]
                ),
            )
        )

    if filters.get("state"):
        val = _as_list(filters["state"])
        if "All India" not in val:
            val.append("All India")
        conditions.append(
            models.FieldCondition(
                key="state",
                match=models.MatchAny(any=val),
            )
        )

    if filters.get("education_level"):
        val = _expand_education_filter(_as_list(filters["education_level"]))
        conditions.append(
            models.FieldCondition(
                key="education_levels",
                match=models.MatchAny(any=val),
            )
        )

    return models.Filter(must=conditions) if conditions else None


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else [value]


def _expand_education_filter(values: list[Any]) -> list[Any]:
    expanded = list(values)
    normalised = {str(value).strip().casefold() for value in values}
    if normalised & {"engineering", "b.tech", "btech", "b.e", "be"}:
        expanded.extend(["UG", "Engineering"])
    if normalised & {"m.tech", "mtech", "m.e", "me", "postgraduate"}:
        expanded.extend(["PG"])
    return list(dict.fromkeys(expanded))


def hybrid_search(
    query_text: str,
    filters: dict[str, Any] | None = None,
    top_k: int = 20,
) -> list[dict]:
    """Run hybrid dense+sparse search with RRF fusion and optional metadata filters.

    Parameters
    ----------
    query_text:
        Free-text query to search for.
    filters:
        Optional dict with keys ``category``, ``state``, ``education_level``
        whose values are strings or lists of strings for MatchAny filtering.
    top_k:
        Maximum number of results to return.

    Returns
    -------
    list[dict]
        Each dict contains ``chunk_id``, ``text``, ``score``, and all payload
        metadata fields from the matching Qdrant point.
    """
    # Embed the query
    dense_vector = get_dense_embedding(query_text)
    sparse_emb = get_sparse_embedding(query_text)

    # Build optional filter
    qdrant_filter = _build_qdrant_filter(filters)

    # Prefetch definitions for each retrieval signal
    dense_prefetch = models.Prefetch(
        query=dense_vector,
        using="dense",
        limit=top_k,
        filter=qdrant_filter,
    )
    sparse_prefetch = models.Prefetch(
        query=models.SparseVector(
            indices=sparse_emb["indices"],
            values=sparse_emb["values"],
        ),
        using="sparse",
        limit=top_k,
        filter=qdrant_filter,
    )

    # Execute fused query
    results = qdrant_client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        prefetch=[dense_prefetch, sparse_prefetch],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=top_k,
    )

    # Normalise into plain dicts
    output: list[dict] = []
    for point in results.points:
        payload = point.payload or {}
        output.append(
            {
                "chunk_id": point.id,
                "text": payload.get("text", ""),
                "score": point.score,
                # Forward all metadata so downstream consumers can use it
                "scheme_id": payload.get("scheme_id"),
                "scheme_name": payload.get("scheme_name"),
                "section": payload.get("section"),
                "categories": payload.get("categories"),
                "income_ceiling": payload.get("income_ceiling"),
                "education_levels": payload.get("education_levels"),
                "state": payload.get("state"),
                "provider": payload.get("provider"),
                "source_url": payload.get("source_url"),
            }
        )

    return output
