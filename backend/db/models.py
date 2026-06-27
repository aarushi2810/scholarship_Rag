"""
SQLAlchemy 2.0 ORM models for ScholarshipRAG.

Tables:
  - users: registered users with profile fields for eligibility matching
  - scholarships: scholarship scheme metadata synced from ingestion
  - eligibility_rules: per-scholarship rule rows for structured filtering
  - saved_scholarships: user bookmark / save-for-later join table
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ── Base ────────────────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


# ── Users ───────────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile fields used for eligibility matching
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    education_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    degree: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cgpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    saved_scholarships: Mapped[list["SavedScholarship"]] = relationship(
        back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


# ── Scholarships ────────────────────────────────────────────────────────────────


class Scholarship(Base):
    __tablename__ = "scholarships"

    id: Mapped[int] = mapped_column(primary_key=True)
    scheme_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    scheme_name: Mapped[str] = mapped_column(String(500), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    categories: Mapped[list] = mapped_column(JSON, default=list)
    income_ceiling: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    education_levels: Mapped[list] = mapped_column(JSON, default=list)
    state: Mapped[str] = mapped_column(String(100), default="All India")
    benefits: Mapped[str] = mapped_column(Text, nullable=False)
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    eligibility_text: Mapped[str] = mapped_column(Text, nullable=False)
    documents_required: Mapped[list] = mapped_column(JSON, default=list)
    application_process: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str] = mapped_column(String(500), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    eligibility_rules: Mapped[list["EligibilityRule"]] = relationship(
        back_populates="scholarship", cascade="all, delete-orphan"
    )
    saved_by: Mapped[list["SavedScholarship"]] = relationship(
        back_populates="scholarship"
    )

    def __repr__(self) -> str:
        return f"<Scholarship id={self.id} scheme={self.scheme_name!r}>"


# ── Eligibility Rules ──────────────────────────────────────────────────────────


class EligibilityRule(Base):
    """Structured eligibility rule for a scholarship.

    rule_type is one of: "category", "income_ceiling", "education_level",
    "state", "gender".
    """

    __tablename__ = "eligibility_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    scholarship_id: Mapped[int] = mapped_column(
        ForeignKey("scholarships.id"), nullable=False
    )
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_value: Mapped[str] = mapped_column(String(200), nullable=False)

    # Relationships
    scholarship: Mapped["Scholarship"] = relationship(
        back_populates="eligibility_rules"
    )

    def __repr__(self) -> str:
        return f"<EligibilityRule {self.rule_type}={self.rule_value!r}>"


# ── Saved Scholarships (join table) ────────────────────────────────────────────


class SavedScholarship(Base):
    __tablename__ = "saved_scholarships"
    __table_args__ = (
        UniqueConstraint("user_id", "scholarship_id", name="uq_saved_user_scholarship"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    scholarship_id: Mapped[int] = mapped_column(
        ForeignKey("scholarships.id"), nullable=False
    )
    saved_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="saved_scholarships")
    scholarship: Mapped["Scholarship"] = relationship(back_populates="saved_by")

    def __repr__(self) -> str:
        return f"<SavedScholarship user={self.user_id} scholarship={self.scholarship_id}>"
