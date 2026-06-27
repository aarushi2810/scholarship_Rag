"""Seed demo scholarships and an Aarushi demo profile."""

from __future__ import annotations

import asyncio
import json
from datetime import date
from pathlib import Path

from sqlalchemy import select

from backend.auth.security import hash_password
from backend.db.models import EligibilityRule, Scholarship, User
from backend.db.postgres import AsyncSessionLocal, init_db

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_schemes.json"


async def main() -> None:
    await init_db()
    schemes = json.loads(DATA_PATH.read_text())

    async with AsyncSessionLocal() as db:
        for item in schemes:
            scholarship = await db.scalar(
                select(Scholarship).where(Scholarship.scheme_id == item["scheme_id"])
            )
            deadline = date.fromisoformat(item["deadline"]) if item.get("deadline") else None
            if scholarship is None:
                scholarship = Scholarship(scheme_id=item["scheme_id"])
                db.add(scholarship)

            scholarship.scheme_name = item["scheme_name"]
            scholarship.provider = item["provider"]
            scholarship.categories = item["categories"]
            scholarship.income_ceiling = item["income_ceiling"]
            scholarship.education_levels = item["education_levels"]
            scholarship.state = item["state"]
            scholarship.benefits = item["benefits"]
            scholarship.deadline = deadline
            scholarship.eligibility_text = item["eligibility_text"]
            scholarship.documents_required = item["documents_required"]
            scholarship.application_process = item["application_process"]
            scholarship.source_url = item["source_url"]

        user = await db.scalar(select(User).where(User.email == "aarushi@example.com"))
        if user is None:
            user = User(
                email="aarushi@example.com",
                hashed_password=hash_password("password123"),
                category="General",
                income=420000,
                education_level="Engineering",
                state="Punjab",
                degree="B.Tech",
                cgpa=8.7,
                gender="Female",
            )
            db.add(user)

        await db.flush()

        # Rebuild simple structured rules from scholarship metadata.
        existing_rules = list((await db.scalars(select(EligibilityRule))).all())
        for rule in existing_rules:
            await db.delete(rule)
        await db.flush()

        scholarships = list((await db.scalars(select(Scholarship))).all())
        for scholarship in scholarships:
            for category in scholarship.categories or []:
                db.add(
                    EligibilityRule(
                        scholarship_id=scholarship.id,
                        rule_type="category",
                        rule_value=category,
                    )
                )
            for level in scholarship.education_levels or []:
                db.add(
                    EligibilityRule(
                        scholarship_id=scholarship.id,
                        rule_type="education_level",
                        rule_value=level,
                    )
                )
            if scholarship.income_ceiling is not None:
                db.add(
                    EligibilityRule(
                        scholarship_id=scholarship.id,
                        rule_type="income_ceiling",
                        rule_value=str(scholarship.income_ceiling),
                    )
                )
            db.add(
                EligibilityRule(
                    scholarship_id=scholarship.id,
                    rule_type="state",
                    rule_value=scholarship.state,
                )
            )

        await db.commit()

    print("Seeded demo scholarships and aarushi@example.com / password123")


if __name__ == "__main__":
    asyncio.run(main())
