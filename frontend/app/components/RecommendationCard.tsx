"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type CSSProperties } from "react";
import { supportLabel, type Recommendation, saveScholarship, unsaveScholarship } from "../../lib/api";

export function RecommendationCard({
  item,
  rank,
  isSavedInitial = false,
}: {
  item: Recommendation;
  rank?: number;
  isSavedInitial?: boolean;
}) {
  const scheme = item.scholarship;
  const router = useRouter();
  const [isSaved, setIsSaved] = useState(isSavedInitial);
  const [loading, setLoading] = useState(false);

  async function handleToggleSave() {
    if (loading) return;
    setLoading(true);
    try {
      if (isSaved) {
        const success = await unsaveScholarship(scheme.scheme_id);
        if (success) {
          setIsSaved(false);
          router.refresh();
        }
      } else {
        const savedItem = await saveScholarship(scheme.scheme_id);
        if (savedItem) {
          setIsSaved(true);
          router.refresh();
        }
      }
    } catch (error) {
      console.error("Failed to toggle save state:", error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <article className="card fade-in">
      <div className="card-head">
        <div className="card-title">
          <div className="provider-mark">{scheme.provider.slice(0, 2).toUpperCase()}</div>
          <div>
            <h3>
              {rank ? `${rank}. ` : ""}
              {scheme.scheme_name}
            </h3>
            <p className="subtle">
              {scheme.provider} · {scheme.state} · {scheme.education_levels.join(", ")}
            </p>
          </div>
        </div>
        <div className="ring" style={{ "--value": item.match_score } as CSSProperties}>
          {item.match_score}%
        </div>
      </div>

      <div className="pill-row">
        <span className="badge emerald">{supportLabel(scheme)}</span>
        <span className="badge cyan">{item.match_score}% Match</span>
        {item.deadline_days_left !== null ? (
          <span className="badge amber">{item.deadline_days_left} Days Remaining</span>
        ) : null}
      </div>

      <p className="subtle">{scheme.benefits}</p>

      <div className="pill-row">
        <span className="pill">{scheme.state}</span>
        {scheme.education_levels.slice(0, 2).map((level) => (
          <span className="pill" key={level}>{level}</span>
        ))}
      </div>

      <div className="reason-list" aria-label="Why recommended">
        {item.reasons.map((reason) => (
          <span className="reason" key={reason}>
            ✓ {reason}
          </span>
        ))}
      </div>

      <div className="actions">
        <Link className="button primary" href={`/scheme/${scheme.scheme_id}`}>
          View Details
        </Link>
        <button
          className={`button ${isSaved ? "emerald" : "ghost"}`}
          type="button"
          onClick={handleToggleSave}
          disabled={loading}
        >
          {isSaved ? "★ Saved" : "☆ Save"}
        </button>
      </div>
    </article>
  );
}

