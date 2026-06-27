"""Transparent rule-based eligibility scoring for scholarship recommendations."""

from __future__ import annotations

from datetime import date

from backend.db.models import Scholarship, User

ALL_INDIA = "all india"


def profile_completion(user: User) -> int:
    fields = [
        user.category,
        user.income,
        user.education_level,
        user.state,
        user.degree,
        user.cgpa,
        user.gender,
    ]
    completed = sum(value is not None and value != "" for value in fields)
    return round((completed / len(fields)) * 100)


def days_until_deadline(deadline: date | None) -> int | None:
    if deadline is None:
        return None
    return (deadline - date.today()).days


def score_scholarship(user: User, scholarship: Scholarship) -> dict:
    reasons: list[str] = []
    missing_or_mismatch: list[str] = []

    category_score = _category_match(user, scholarship, reasons, missing_or_mismatch)
    income_score = _income_match(user, scholarship, reasons, missing_or_mismatch)
    education_score = _education_match(user, scholarship, reasons, missing_or_mismatch)
    state_score = _state_match(user, scholarship, reasons, missing_or_mismatch)
    deadline_score = _deadline_score(scholarship, reasons, missing_or_mismatch)

    hard_eligibility = min(category_score, income_score, education_score)
    if hard_eligibility <= 0:
        weighted_score = 0
    else:
        weighted_score = 100 * (
            0.50 * hard_eligibility
            + 0.25 * education_score
            + 0.15 * state_score
            + 0.10 * deadline_score
        )

    return {
        "scholarship": scholarship,
        "match_score": round(weighted_score),
        "deadline_days_left": days_until_deadline(scholarship.deadline),
        "reasons": reasons,
        "missing_or_mismatch": missing_or_mismatch,
    }


def _normalise(value: str | None) -> str:
    return (value or "").strip().casefold()


def _normalised_list(values: list | None) -> set[str]:
    return {_normalise(str(value)) for value in (values or []) if value}


def _user_education_tokens(user: User) -> set[str]:
    tokens = {_normalise(user.education_level), _normalise(user.degree)}
    joined = " ".join(token for token in tokens if token)
    if any(term in joined for term in ("b.tech", "btech", "b.e", "be ", "engineering")):
        tokens.update({"ug", "undergraduate", "engineering"})
    if any(term in joined for term in ("m.tech", "mtech", "m.e", "masters", "postgraduate")):
        tokens.update({"pg", "postgraduate"})
    return {token for token in tokens if token}


def _category_match(
    user: User,
    scholarship: Scholarship,
    reasons: list[str],
    missing_or_mismatch: list[str],
) -> float:
    categories = _normalised_list(scholarship.categories)
    if not categories or "all" in categories:
        reasons.append("Open category eligible")
        return 1.0
    if not user.category:
        missing_or_mismatch.append("Add category to confirm eligibility")
        return 0.5
    if _normalise(user.category) in categories:
        reasons.append(f"{user.category} category eligible")
        return 1.0
    missing_or_mismatch.append("Category does not match this scheme")
    return 0.0


def _income_match(
    user: User,
    scholarship: Scholarship,
    reasons: list[str],
    missing_or_mismatch: list[str],
) -> float:
    if scholarship.income_ceiling is None:
        reasons.append("No income ceiling listed")
        return 1.0
    if user.income is None:
        missing_or_mismatch.append("Add family income to confirm eligibility")
        return 0.5
    if user.income <= scholarship.income_ceiling:
        reasons.append("Income eligible")
        return 1.0
    missing_or_mismatch.append("Income is above the listed ceiling")
    return 0.0


def _education_match(
    user: User,
    scholarship: Scholarship,
    reasons: list[str],
    missing_or_mismatch: list[str],
) -> float:
    levels = _normalised_list(scholarship.education_levels)
    if not levels:
        reasons.append("No education-level restriction listed")
        return 1.0
    if not user.education_level and not user.degree:
        missing_or_mismatch.append("Add education level to confirm eligibility")
        return 0.5

    user_tokens = _user_education_tokens(user)
    if user_tokens & levels:
        display = user.degree or user.education_level or "Matching education level"
        reasons.append(f"{display} student")
        return 1.0
    if any(level in token or token in level for level in levels for token in user_tokens):
        display = user.degree or user.education_level or "Related education level"
        reasons.append(f"{display} student")
        return 0.8

    missing_or_mismatch.append("Education level does not match this scheme")
    return 0.0


def _state_match(
    user: User,
    scholarship: Scholarship,
    reasons: list[str],
    missing_or_mismatch: list[str],
) -> float:
    scheme_state = _normalise(scholarship.state)
    if not scheme_state or scheme_state == ALL_INDIA:
        reasons.append("Available across India")
        return 0.8
    if not user.state:
        missing_or_mismatch.append("Add state to confirm residence match")
        return 0.5
    if _normalise(user.state) == scheme_state:
        reasons.append(f"{scholarship.state} resident")
        return 1.0
    missing_or_mismatch.append(f"Scheme is limited to {scholarship.state}")
    return 0.0


def _deadline_score(
    scholarship: Scholarship,
    reasons: list[str],
    missing_or_mismatch: list[str],
) -> float:
    days_left = days_until_deadline(scholarship.deadline)
    if days_left is None:
        return 0.5
    if days_left < 0:
        missing_or_mismatch.append("Deadline has passed")
        return 0.0
    if days_left <= 30:
        reasons.append(f"Deadline in {days_left} days")
        return 1.0
    if days_left <= 90:
        reasons.append(f"Deadline in {days_left} days")
        return 0.8
    return 0.6
