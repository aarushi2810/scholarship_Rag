"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import {
  formatIncome,
  semanticSearch,
  supportLabel,
  saveScholarship,
  unsaveScholarship,
  type SearchResult,
} from "../../lib/api";

/* ── Debounce hook ─────────────────────────────────────────────────────────── */
function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

/* ── Skeleton card (shown while loading) ───────────────────────────────────── */
function SkeletonCard() {
  return (
    <div className="card skeleton-card" aria-hidden="true">
      <div className="skeleton skeleton--title" />
      <div className="skeleton skeleton--line" />
      <div className="skeleton skeleton--line skeleton--short" />
    </div>
  );
}

/* ── Individual search result card ─────────────────────────────────────────── */
function SearchResultCard({ result }: { result: SearchResult }) {
  const scheme = result.scholarship;
  const [isSaved, setIsSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  async function handleToggleSave() {
    if (saving) return;
    setSaving(true);
    try {
      if (isSaved) {
        await unsaveScholarship(scheme.scheme_id);
        setIsSaved(false);
      } else {
        await saveScholarship(scheme.scheme_id);
        setIsSaved(true);
      }
    } finally {
      setSaving(false);
    }
  }

  const days = result.deadline_days_left;
  const deadlineUrgent = days !== null && days <= 7;
  const deadlineWarning = days !== null && days > 7 && days <= 30;

  return (
    <article className="card fade-in">
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

        {/* Match % ring — only for authenticated users */}
        {result.match_score !== null ? (
          <div
            className="ring"
            style={{ "--value": result.match_score } as CSSProperties}
            title={`${result.match_score}% match with your profile`}
          >
            {result.match_score}%
          </div>
        ) : null}
      </div>

      <p className="subtle">{scheme.benefits}</p>

      <div className="pill-row">
        <span className="badge emerald">{supportLabel(scheme)}</span>
        {result.match_score !== null && (
          <span className="badge cyan">{result.match_score}% Match</span>
        )}
        {deadlineUrgent && (
          <span className="badge rose">🔴 Closes in {days} days</span>
        )}
        {deadlineWarning && (
          <span className="badge amber">⏰ {days} days left</span>
        )}
        {days === null && <span className="badge">No deadline listed</span>}
        {scheme.categories.map((cat) => (
          <span className="pill" key={cat}>{cat}</span>
        ))}
      </div>

      {/* Eligibility reasons (authenticated only) */}
      {result.reasons.length > 0 && (
        <div className="reason-list">
          {result.reasons.map((r) => (
            <span className="reason" key={r}>✓ {r}</span>
          ))}
        </div>
      )}

      {/* Missing / mismatch warnings */}
      {result.missing_or_mismatch.length > 0 && (
        <div className="mismatch-list">
          {result.missing_or_mismatch.map((note) => (
            <span className="mismatch" key={note}>⚠ {note}</span>
          ))}
        </div>
      )}

      <div className="actions">
        <Link className="button primary" href={`/scheme/${scheme.scheme_id}`}>
          Details
        </Link>
        <button
          className={`button ${isSaved ? "emerald" : "ghost"}`}
          type="button"
          onClick={handleToggleSave}
          disabled={saving}
        >
          {isSaved ? "★ Saved" : "☆ Save"}
        </button>
      </div>
    </article>
  );
}

/* ── Sort helper (client-side, no network request) ─────────────────────────── */
function sortResults(results: SearchResult[], sort: "match" | "deadline"): SearchResult[] {
  const copy = [...results];
  if (sort === "deadline") {
    copy.sort((a, b) => {
      const da = a.deadline_days_left ?? 9999;
      const db = b.deadline_days_left ?? 9999;
      return da - db;
    });
  } else {
    // "match" — sort by match_score desc, fall back to semantic_score
    copy.sort((a, b) => {
      const ma = a.match_score ?? a.semantic_score * 100;
      const mb = b.match_score ?? b.semantic_score * 100;
      return mb - ma;
    });
  }
  return copy;
}

/* ── Main search component ──────────────────────────────────────────────────── */
export function SearchClient() {
  const [query, setQuery] = useState("");
  const [state, setState] = useState("");
  const [category, setCategory] = useState("");
  const [education, setEducation] = useState("");
  const [sort, setSort] = useState<"match" | "deadline">("match");

  // Raw results from the server (unsorted, cached by query+filters)
  const [rawResults, setRawResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  // Debounce the text query at 400ms
  const debouncedQuery = useDebounce(query, 400);

  // Debounce the filter tuple at 300ms so rapid dropdown changes don't fire
  // multiple requests
  const filterTuple = useMemo(
    () => ({ state, category, education }),
    [state, category, education],
  );
  const debouncedFilters = useDebounce(filterTuple, 300);

  // Track the last request params to avoid duplicate fetches
  const lastFetchRef = useRef<string>("");

  const runSearch = useCallback(async () => {
    const fetchKey = JSON.stringify({
      q: debouncedQuery,
      ...debouncedFilters,
    });

    // Skip if nothing changed since the last fetch
    if (fetchKey === lastFetchRef.current && hasSearched) return;
    lastFetchRef.current = fetchKey;

    setLoading(true);
    setHasSearched(true);
    try {
      const data = await semanticSearch(debouncedQuery, {
        state: debouncedFilters.state || undefined,
        category: debouncedFilters.category || undefined,
        education_level: debouncedFilters.education || undefined,
        // Do NOT pass sort to the server — we sort client-side so the
        // cached result can be re-sorted without a new network request.
      });
      setRawResults(data);
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, debouncedFilters, hasSearched]);

  // Re-run search whenever debounced query or filters change
  useEffect(() => {
    runSearch();
  }, [runSearch]);

  // Client-side sort — no network request needed
  const results = useMemo(() => sortResults(rawResults, sort), [rawResults, sort]);

  return (
    <>
      <section className="panel" id="advisor">
        <div className="inline-head">
          <div>
            <p className="eyebrow">Scholarship Search</p>
            <h2>Results update as you type</h2>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            {!loading && hasSearched && (
              <span className="badge cyan">{results.length} Results</span>
            )}
            {/* Sort toggle — now purely client-side, no network request */}
            <div className="sort-toggle">
              <button
                type="button"
                className={`sort-toggle__btn ${sort === "match" ? "sort-toggle__btn--active" : ""}`}
                onClick={() => setSort("match")}
              >
                Best Match
              </button>
              <button
                type="button"
                className={`sort-toggle__btn ${sort === "deadline" ? "sort-toggle__btn--active" : ""}`}
                onClick={() => setSort("deadline")}
              >
                Deadline
              </button>
            </div>
          </div>
        </div>

        <div className="filters">
          <input
            className="field"
            placeholder="e.g. girl engineering student Punjab…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
          <select className="field" value={state} onChange={(e) => setState(e.target.value)}>
            <option value="">Any state</option>
            <option value="Punjab">Punjab</option>
            <option value="All India">All India</option>
          </select>
          <select className="field" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">Any category</option>
            <option value="General">General</option>
            <option value="OBC">OBC</option>
            <option value="SC">SC</option>
            <option value="ST">ST</option>
          </select>
          <select className="field" value={education} onChange={(e) => setEducation(e.target.value)}>
            <option value="">Any education</option>
            <option value="UG">UG</option>
            <option value="PG">PG</option>
            <option value="Engineering">Engineering</option>
            <option value="Diploma">Diploma</option>
          </select>
        </div>
      </section>

      <section className="stack">
        {loading ? (
          Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)
        ) : results.length === 0 && hasSearched ? (
          <div className="panel" style={{ textAlign: "center", padding: "40px" }}>
            <p className="subtle">No scholarships found. Try adjusting your filters.</p>
          </div>
        ) : (
          results.map((result) => (
            <SearchResultCard key={result.scholarship.scheme_id} result={result} />
          ))
        )}
      </section>
    </>
  );
}
