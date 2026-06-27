"""
Chunker: splits each SchemeMetadata into section-level SchemeChunks.

Each scheme produces exactly 4 chunks:
  1. eligibility          – eligibility_text
  2. benefits             – benefits description
  3. documents_required   – bullet-formatted document list
  4. application_process  – how-to-apply text

Every chunk carries a flat metadata dict for vector-store filtering.
"""

from __future__ import annotations

from ingestion.schema import SchemeChunk, SchemeMetadata


# ── helpers ──────────────────────────────────────────────────────────

def _build_metadata(scheme: SchemeMetadata, section: str) -> dict:
    """Build a flat metadata dict suitable for Qdrant payload."""
    return {
        "scheme_id": scheme.scheme_id,
        "scheme_name": scheme.scheme_name,
        "categories": scheme.categories,
        "state": scheme.state,
        "education_levels": scheme.education_levels,
        "income_ceiling": scheme.income_ceiling,
        "provider": scheme.provider,
        "section": section,
        "source_url": scheme.source_url,
        "deadline": scheme.deadline,
    }


def _format_documents_list(docs: list[str]) -> str:
    """Turn a list of document names into a readable bulleted string."""
    header = "Documents required for this scholarship:\n"
    bullets = "\n".join(f"- {doc}" for doc in docs)
    return header + bullets


# ── public API ───────────────────────────────────────────────────────

def chunk_scheme(scheme: SchemeMetadata) -> list[SchemeChunk]:
    """
    Split a single SchemeMetadata into 4 section chunks.

    Returns:
        List of 4 SchemeChunk objects.
    """
    sections: dict[str, str] = {
        "eligibility": scheme.eligibility_text,
        "benefits": scheme.benefits,
        "documents_required": _format_documents_list(scheme.documents_required),
        "application_process": scheme.application_process,
    }

    chunks: list[SchemeChunk] = []
    for section_name, text in sections.items():
        chunk = SchemeChunk(
            chunk_id=f"{scheme.scheme_id}__{section_name}",
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.scheme_name,
            section=section_name,
            text=f"[{scheme.scheme_name}] {text}",
            metadata=_build_metadata(scheme, section_name),
        )
        chunks.append(chunk)
    return chunks


def chunk_all_schemes(schemes: list[SchemeMetadata]) -> list[SchemeChunk]:
    """
    Chunk every scheme in the list.

    Returns:
        Flat list of all SchemeChunks across all schemes.
    """
    all_chunks: list[SchemeChunk] = []
    for scheme in schemes:
        all_chunks.extend(chunk_scheme(scheme))
    return all_chunks
