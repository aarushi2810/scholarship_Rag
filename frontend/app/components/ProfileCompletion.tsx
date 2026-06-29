"use client";

import Link from "next/link";

const FIELD_LABELS: Record<string, string> = {
  category: "Caste / Category",
  income: "Family Income",
  education_level: "Education Level",
  state: "Home State",
  degree: "Degree / Course",
  cgpa: "CGPA / Percentage",
  gender: "Gender",
};

type ProfileFields = {
  category: string | null;
  income: number | null;
  education_level: string | null;
  state: string | null;
  degree: string | null;
  cgpa: number | null;
  gender: string | null;
};

function getMissingFields(fields: Partial<ProfileFields>): string[] {
  return Object.entries(FIELD_LABELS)
    .filter(([key]) => {
      const val = fields[key as keyof ProfileFields];
      return val === null || val === undefined || val === "";
    })
    .map(([, label]) => label);
}

export function ProfileCompletion({
  completion,
  profile,
}: {
  completion: number;
  profile: Partial<ProfileFields>;
}) {
  const missing = getMissingFields(profile);
  const isComplete = missing.length === 0;

  return (
    <section className="panel profile-completion-panel">
      <div className="metric-row">
        <div>
          <h2>Profile Completion</h2>
          <p className="subtle">
            {isComplete
              ? "Your profile is fully set up."
              : "Complete your profile for better matches."}
          </p>
        </div>
        <div
          className="ring"
          style={{ "--value": completion } as React.CSSProperties}
          aria-label={`Profile ${completion}% complete`}
        >
          {completion}%
        </div>
      </div>

      <div className="progress" aria-label={`Profile completion ${completion}%`}>
        <span style={{ width: `${completion}%` }} />
      </div>

      {missing.length > 0 && (
        <div className="profile-missing">
          <p className="profile-missing__label">Missing fields:</p>
          <ul className="profile-missing__list">
            {missing.map((field) => (
              <li key={field} className="profile-missing__item">
                <span className="profile-missing__dot" />
                {field}
              </li>
            ))}
          </ul>
          <Link href="/profile" className="button primary profile-missing__cta">
            Complete Profile →
          </Link>
        </div>
      )}
    </section>
  );
}
