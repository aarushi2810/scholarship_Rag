"""Index curated scholarship data into Qdrant and train sparse retrieval.

Run:
    python -m ingestion.index_data
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from backend.config import settings
from ingestion.chunker import chunk_all_schemes
from ingestion.schema import SchemeMetadata

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "sample_schemes.json"
VECTORIZER_PATH = ROOT / "data" / "tfidf_vectorizer.pkl"


def load_schemes(path: Path = DATA_PATH) -> list[SchemeMetadata]:
    raw = json.loads(path.read_text())
    return [SchemeMetadata.model_validate(item) for item in raw]


def point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"scholarshiprag:{chunk_id}"))


def main() -> None:
    from qdrant_client import QdrantClient, models

    from ingestion.embedder import SchemeEmbedder

    schemes = load_schemes()
    chunks = chunk_all_schemes(schemes)
    texts = [chunk.text for chunk in chunks]

    embedder = SchemeEmbedder(settings.EMBEDDING_MODEL)
    embedder.fit_sparse(texts)
    sparse_vectors = embedder.embed_sparse(texts)
    embedder.save_sparse_vectorizer(VECTORIZER_PATH)
    dense_vectors = embedder.embed_dense(texts)

  
    client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
)
    client.recreate_collection(
        collection_name=settings.QDRANT_COLLECTION,
        vectors_config={
            "dense": models.VectorParams(
                size=settings.EMBEDDING_DIM,
                distance=models.Distance.COSINE,
            )
        },
        sparse_vectors_config={
            "sparse": models.SparseVectorParams(
                index=models.SparseIndexParams(on_disk=False)
            )
        },
    )

    points: list[models.PointStruct] = []
    for chunk, dense, sparse in zip(chunks, dense_vectors, sparse_vectors, strict=True):
        points.append(
            models.PointStruct(
                id=point_id(chunk.chunk_id),
                vector={
                    "dense": dense,
                    "sparse": models.SparseVector(
                        indices=sparse["indices"],
                        values=sparse["values"],
                    ),
                },
                payload={**chunk.metadata, "chunk_id": chunk.chunk_id, "text": chunk.text},
            )
        )

    client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
    print(
        f"Indexed {len(chunks)} chunks from {len(schemes)} schemes into "
        f"{settings.QDRANT_COLLECTION}; saved {VECTORIZER_PATH}"
    )


if __name__ == "__main__":
    main()
