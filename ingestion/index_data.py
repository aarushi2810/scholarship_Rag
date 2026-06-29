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

    print("Loading scholarship dataset...")

    schemes = load_schemes()
    chunks = chunk_all_schemes(schemes)
    texts = [chunk.text for chunk in chunks]

    print(f"Loaded {len(schemes)} schemes")
    print(f"Generated {len(chunks)} chunks")

    # -----------------------------
    # Generate embeddings
    # -----------------------------
    embedder = SchemeEmbedder(settings.EMBEDDING_MODEL)

    print("Training TF-IDF vectorizer...")
    embedder.fit_sparse(texts)

    sparse_vectors = embedder.embed_sparse(texts)
    embedder.save_sparse_vectorizer(VECTORIZER_PATH)

    print("Generating dense embeddings...")
    dense_vectors = embedder.embed_dense(texts)

    # -----------------------------
    # Connect to Qdrant Cloud
    # -----------------------------
    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        timeout=300,
    )

    print("Preparing Qdrant collection...")

    if client.collection_exists(settings.QDRANT_COLLECTION):
        client.delete_collection(settings.QDRANT_COLLECTION)

    client.create_collection(
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

    # -----------------------------
    # Build points
    # -----------------------------
    points: list[models.PointStruct] = []

    for chunk, dense, sparse in zip(
        chunks,
        dense_vectors,
        sparse_vectors,
        strict=True,
    ):
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
                payload={
                    **chunk.metadata,
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                },
            )
        )

    print(f"Uploading {len(points)} vectors to Qdrant...")

    # -----------------------------
    # Upload in batches
    # -----------------------------
    BATCH_SIZE = 20

    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i : i + BATCH_SIZE]

        client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=batch,
            wait=True,
        )

        print(
            f"Uploaded {min(i + BATCH_SIZE, len(points))}/{len(points)} vectors"
        )

    print("\n Indexing completed successfully!")

    print(
        f"Indexed {len(chunks)} chunks from {len(schemes)} schemes into "
        f"'{settings.QDRANT_COLLECTION}'"
    )

    print(f"TF-IDF vectorizer saved to: {VECTORIZER_PATH}")


if __name__ == "__main__":
    main()
