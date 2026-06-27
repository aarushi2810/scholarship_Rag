"""Manual retrieval smoke test for the curated scholarship corpus.

Default mode runs a local TF-IDF check without Qdrant. Use ``--qdrant`` after
``python -m ingestion.index_data`` to test the actual backend hybrid search.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.chunker import chunk_all_schemes
from ingestion.schema import SchemeMetadata

DATA_PATH = ROOT / "data" / "sample_schemes.json"


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    expected_scheme_ids: set[str]
    filters: dict | None = None


CASES = [
    RetrievalCase(
        query="scholarships for female engineering students",
        expected_scheme_ids={"aicte_pragati", "nsp_merit_punjab"},
        filters={"education_level": "Engineering"},
    ),
    RetrievalCase(
        query="scholarships in Punjab",
        expected_scheme_ids={"nsp_merit_punjab", "punjab_post_matric_sc"},
        filters={"state": "Punjab"},
    ),
    RetrievalCase(
        query="scholarships under income ceiling 2 lakh",
        expected_scheme_ids={"punjab_post_matric_sc"},
    ),
    RetrievalCase(
        query="UGC undergraduate scholarship",
        expected_scheme_ids={"ugc_ishan_uday"},
        filters={"education_level": "UG"},
    ),
]


def load_schemes() -> list[SchemeMetadata]:
    raw = json.loads(DATA_PATH.read_text())
    return [SchemeMetadata.model_validate(item) for item in raw]


def run_local(top_k: int) -> int:
    chunks = chunk_all_schemes(load_schemes())
    texts = [chunk.text for chunk in chunks]
    vectorizer = TfidfVectorizer(max_features=30_000, sublinear_tf=True)
    matrix = vectorizer.fit_transform(texts)

    passes = 0
    for case in CASES:
        query_vector = vectorizer.transform([case.query])
        scores = cosine_similarity(query_vector, matrix).ravel()
        ranked_indexes = scores.argsort()[::-1]
        hits = _dedupe_hits(chunks, scores, ranked_indexes, top_k)
        passed = _passed(hits, case.expected_scheme_ids)
        passes += int(passed)
        _print_case(case.query, hits, case.expected_scheme_ids, passed)
    return passes


def run_qdrant(top_k: int) -> int:
    from backend.db.vector_store import hybrid_search

    passes = 0
    for case in CASES:
        results = hybrid_search(case.query, filters=case.filters, top_k=top_k)
        hits = [
            (
                str(result.get("scheme_id")),
                str(result.get("scheme_name")),
                round(float(result.get("score") or 0), 4),
            )
            for result in results
        ]
        passed = _passed(hits, case.expected_scheme_ids)
        passes += int(passed)
        _print_case(case.query, hits, case.expected_scheme_ids, passed)
    return passes


def _dedupe_hits(chunks, scores, ranked_indexes, top_k: int) -> list[tuple[str, str, float]]:
    hits = []
    seen = set()
    for index in ranked_indexes:
        chunk = chunks[index]
        if chunk.scheme_id in seen:
            continue
        seen.add(chunk.scheme_id)
        hits.append((chunk.scheme_id, chunk.scheme_name, round(float(scores[index]), 4)))
        if len(hits) == top_k:
            break
    return hits


def _passed(hits: list[tuple[str, str, float]], expected: set[str]) -> bool:
    return bool({scheme_id for scheme_id, _, _ in hits} & expected)


def _print_case(
    query: str,
    hits: list[tuple[str, str, float]],
    expected: set[str],
    passed: bool,
) -> None:
    status = "PASS" if passed else "FAIL"
    print(f"\n[{status}] {query}")
    print(f"Expected one of: {', '.join(sorted(expected))}")
    for scheme_id, name, score in hits[:5]:
        print(f"  - {scheme_id}: {name} ({score})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qdrant", action="store_true", help="Use backend hybrid_search")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    passes = run_qdrant(args.top_k) if args.qdrant else run_local(args.top_k)
    total = len(CASES)
    print(f"\nRetrieval smoke test: {passes}/{total} representative queries passed")
    if passes != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
