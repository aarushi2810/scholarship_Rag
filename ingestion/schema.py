"""
Pydantic schemas for scholarship ingestion pipeline.

SchemeMetadata  – represents one scholarship scheme (mirrors sample_schemes.json).
SchemeChunk     – represents a single text chunk derived from a scheme,
                  ready for embedding and vector-store upsert.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SchemeMetadata(BaseModel):
    """Full metadata for a single scholarship scheme."""

    scheme_id: str = Field(..., description="Unique identifier, e.g. 'nsp_sc_postmatric'")
    scheme_name: str = Field(..., description="Official name of the scholarship scheme")
    provider: str = Field(..., description="'Central', 'State', 'UGC', 'AICTE', etc.")
    categories: list[str] = Field(..., description="Eligible social categories, e.g. ['SC', 'ST']")
    income_ceiling: float | None = Field(None, description="Max annual family income in INR, or null")
    education_levels: list[str] = Field(..., description="Eligible levels, e.g. ['UG', 'PG']")
    state: str = Field(..., description="'All India' or specific state name")
    benefits: str = Field(..., description="Description of financial / other benefits")
    deadline: str | None = Field(None, description="Application deadline as YYYY-MM-DD or null")
    eligibility_text: str = Field(..., description="Detailed eligibility criteria paragraph")
    documents_required: list[str] = Field(..., description="List of required document names")
    application_process: str = Field(..., description="Step-by-step application instructions")
    source_url: str = Field(..., description="Official government portal URL")


class SchemeChunk(BaseModel):
    """A single text chunk derived from a SchemeMetadata record."""

    chunk_id: str = Field(..., description="Globally unique chunk id, e.g. 'nsp_sc_postmatric__eligibility'")
    scheme_id: str = Field(..., description="Parent scheme identifier")
    scheme_name: str = Field(..., description="Parent scheme name (denormalised for retrieval)")
    section: str = Field(..., description="Section label: eligibility | benefits | documents_required | application_process")
    text: str = Field(..., description="The actual text content of the chunk")
    metadata: dict = Field(default_factory=dict, description="Flat key-value metadata carried into vector store payload")
