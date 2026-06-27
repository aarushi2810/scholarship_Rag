"""
SchemeEmbedder – produces dense and sparse vectors for Qdrant hybrid search.

Dense  : BAAI/bge-small-en-v1.5  (384-d, cosine-normalised)
Sparse : sklearn TfidfVectorizer → indices/values dict compatible with
         qdrant_client.models.SparseVector
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer


class SchemeEmbedder:
    """Wraps dense + sparse embedding for the scholarship corpus."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        self._dense_model = SentenceTransformer(model_name)
        self._tfidf: TfidfVectorizer | None = None  # fitted lazily

    # ── dense ────────────────────────────────────────────────────────

    def embed_dense(self, texts: list[str]) -> list[list[float]]:
        """Batch-encode texts into L2-normalised dense vectors."""
        embeddings = self._dense_model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        # embeddings is ndarray of shape (n, 384)
        return embeddings.tolist()

    def embed_dense_single(self, text: str) -> list[float]:
        """Encode a single text into a dense vector."""
        embedding = self._dense_model.encode(
            [text],
            normalize_embeddings=True,
        )
        return embedding[0].tolist()

    # ── sparse (TF-IDF) ─────────────────────────────────────────────

    def fit_sparse(self, texts: list[str]) -> None:
        """Fit the TF-IDF vectorizer on the corpus. Must be called before
        embed_sparse / embed_sparse_single."""
        self._tfidf = TfidfVectorizer(
            max_features=30_000,
            sublinear_tf=True,
            dtype=np.float32,
        )
        self._tfidf.fit(texts)

    def save_sparse_vectorizer(self, path: str | Path) -> None:
        """Persist the fitted TF-IDF vectorizer for query-time sparse search."""
        if self._tfidf is None:
            raise RuntimeError("Cannot save TF-IDF vectorizer before fitting it.")
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as fh:
            pickle.dump(self._tfidf, fh)

    def embed_sparse(self, texts: list[str]) -> list[dict]:
        """
        Transform texts into sparse vectors.

        If the vectorizer has not been fitted yet, it will be fitted on
        the provided texts (corpus-level call).

        Returns:
            list of dicts with 'indices' (list[int]) and 'values' (list[float]).
        """
        if self._tfidf is None:
            self.fit_sparse(texts)

        sparse_matrix = self._tfidf.transform(texts)  # type: ignore[union-attr]

        results: list[dict] = []
        for i in range(sparse_matrix.shape[0]):
            row = sparse_matrix.getrow(i)
            indices = row.indices.tolist()
            values = row.data.tolist()
            results.append({"indices": indices, "values": values})
        return results

    def embed_sparse_single(self, text: str) -> dict:
        """
        Transform a single text into a sparse vector.

        Raises:
            RuntimeError: if the vectorizer hasn't been fitted yet.
        """
        if self._tfidf is None:
            raise RuntimeError(
                "TF-IDF vectorizer not fitted. Call fit_sparse() or "
                "embed_sparse() on the corpus first."
            )
        row = self._tfidf.transform([text]).getrow(0)
        return {
            "indices": row.indices.tolist(),
            "values": row.data.tolist(),
        }
