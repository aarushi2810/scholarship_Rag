"""Pydantic request/response schemas for the product API."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileUpdate(BaseModel):
    category: str | None = None
    income: float | None = Field(default=None, ge=0)
    education_level: str | None = None
    state: str | None = None
    degree: str | None = None
    cgpa: float | None = Field(default=None, ge=0, le=10)
    gender: str | None = None


class UserProfile(ProfileUpdate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    profile_completion: int


class ScholarshipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scheme_id: str
    scheme_name: str
    provider: str
    categories: list[str]
    income_ceiling: float | None
    education_levels: list[str]
    state: str
    benefits: str
    deadline: date | None
    eligibility_text: str
    documents_required: list[str]
    application_process: str
    source_url: str


class RecommendationRead(BaseModel):
    scholarship: ScholarshipRead
    match_score: int
    deadline_days_left: int | None
    reasons: list[str]
    missing_or_mismatch: list[str]
    urgency_boost: bool = False


class SearchResult(BaseModel):
    scholarship: ScholarshipRead
    match_score: int | None  # None for anonymous users
    semantic_score: float
    deadline_days_left: int | None
    reasons: list[str]
    missing_or_mismatch: list[str]


class SavedScholarshipRead(BaseModel):
    id: int
    saved_at: datetime
    scholarship: ScholarshipRead
    deadline_days_left: int | None


class DashboardRead(BaseModel):
    name: str
    profile_completion: int
    top_matches: list[RecommendationRead]
    saved_scholarships: list[SavedScholarshipRead]
    # Profile fields for the completion widget
    category: str | None = None
    income: float | None = None
    education_level: str | None = None
    state: str | None = None
    degree: str | None = None
    cgpa: float | None = None
    gender: str | None = None


class ChatSource(BaseModel):
    scheme_id: str
    scheme_name: str
    source_url: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]


