"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { formatIncome, supportLabel, type Scholarship } from "../../lib/api";
import { SaveButton } from "../components/SaveButton";


export function SearchClient({ schemes }: { schemes: Scholarship[] }) {
  const [query, setQuery] = useState("");
  const [state, setState] = useState("");
  const [category, setCategory] = useState("");
  const [education, setEducation] = useState("");

  const filtered = useMemo(() => {
    const normalisedQuery = query.trim().toLowerCase();
    return schemes.filter((scheme) => {
      const text = `${scheme.scheme_name} ${scheme.provider} ${scheme.benefits} ${scheme.eligibility_text}`.toLowerCase();
      const matchesQuery = !normalisedQuery || text.includes(normalisedQuery);
      const matchesState = !state || scheme.state === state || scheme.state === "All India";
      const matchesCategory = !category || scheme.categories.includes(category);
      const matchesEducation = !education || scheme.education_levels.includes(education);
      return matchesQuery && matchesState && matchesCategory && matchesEducation;
    });
  }, [category, education, query, schemes, state]);

  return (
    <>
      <section className="panel" id="advisor">
        <div className="inline-head">
          <div>
            <p className="eyebrow">Scholarship Search Workspace</p>
            <h2>Results update as you type</h2>
          </div>
          <span className="badge cyan">{filtered.length} Results</span>
        </div>
        <div className="filters">
          <input className="field" placeholder="Female engineering student from Punjab" value={query} onChange={(event) => setQuery(event.target.value)} />
          <select className="field" value={state} onChange={(event) => setState(event.target.value)}>
            <option value="">Any state</option>
            <option value="Punjab">Punjab</option>
            <option value="All India">All India</option>
          </select>
          <select className="field" value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">Any category</option>
            <option value="General">General</option>
            <option value="OBC">OBC</option>
            <option value="SC">SC</option>
            <option value="ST">ST</option>
          </select>
          <select className="field" value={education} onChange={(event) => setEducation(event.target.value)}>
            <option value="">Any education</option>
            <option value="UG">UG</option>
            <option value="PG">PG</option>
            <option value="Engineering">Engineering</option>
            <option value="Diploma">Diploma</option>
          </select>
        </div>
      </section>

      <section className="stack">
        {filtered.map((scheme) => (
          <article className="card fade-in" key={scheme.scheme_id}>
            <div className="card-head">
              <div className="card-title">
                <div className="provider-mark">{scheme.provider.slice(0, 2).toUpperCase()}</div>
                <div>
                  <h3>{scheme.scheme_name}</h3>
                  <p className="subtle">
                    {scheme.provider} · {scheme.state} · {formatIncome(scheme.income_ceiling)}
                  </p>
                </div>
              </div>
              <div className="actions">
                <Link className="button primary" href={`/scheme/${scheme.scheme_id}`}>
                  Details
                </Link>
                <SaveButton schemeId={scheme.scheme_id} />
              </div>
            </div>
            <p className="subtle">{scheme.benefits}</p>
            <div className="pill-row">
              <span className="badge emerald">{supportLabel(scheme)}</span>
              <span className="badge amber">{scheme.deadline ? "Deadline Listed" : "No Deadline"}</span>
              {scheme.categories.map((item) => (
                <span className="pill" key={item}>{item}</span>
              ))}
              {scheme.education_levels.map((item) => (
                <span className="pill" key={item}>{item}</span>
              ))}
            </div>
          </article>
        ))}
      </section>
    </>
  );
}
