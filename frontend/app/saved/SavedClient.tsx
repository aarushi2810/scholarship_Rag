"use client";

import Link from "next/link";
import { useState } from "react";
import { unsaveScholarship, formatIncome, type SavedScholarship } from "../../lib/api";

function getStatusLabel(days: number | null): { label: string; cls: string } {
  if (days === null) return { label: "No Deadline", cls: "" };
  if (days < 0) return { label: "Closed", cls: "status--closed" };
  if (days <= 7) return { label: "Closing Soon", cls: "status--critical" };
  if (days <= 30) return { label: "Ending Soon", cls: "status--warning" };
  return { label: "Open", cls: "status--open" };
}

export function SavedClient({
  initialSaved,
}: {
  initialSaved: SavedScholarship[];
}) {
  const [saved, setSaved] = useState(initialSaved);
  const [removing, setRemoving] = useState<string | null>(null);

  async function handleUnsave(schemeId: string) {
    setRemoving(schemeId);
    try {
      const ok = await unsaveScholarship(schemeId);
      if (ok) {
        setSaved((prev) =>
          prev.filter((s) => s.scholarship.scheme_id !== schemeId),
        );
      }
    } finally {
      setRemoving(null);
    }
  }

  if (saved.length === 0) {
    return (
      <div className="panel" style={{ textAlign: "center", padding: "48px 24px" }}>
        <p style={{ fontSize: "32px", marginBottom: "12px" }}>📭</p>
        <h3>No saved scholarships yet</h3>
        <p className="subtle">
          Browse scholarships and save the ones you want to apply for.
        </p>
        <Link className="button primary" href="/search" style={{ marginTop: "16px", display: "inline-flex" }}>
          Search Scholarships
        </Link>
      </div>
    );
  }

  return (
    <div className="saved-table-wrapper">
      {/* Header row */}
      <div className="saved-table-header">
        <span>Scholarship</span>
        <span>Provider</span>
        <span>Deadline</span>
        <span>Status</span>
        <span />
      </div>

      <div className="stack">
        {saved.map((item) => {
          const scheme = item.scholarship;
          const days = item.deadline_days_left;
          const status = getStatusLabel(days);

          return (
            <div className="card saved-table-row" key={item.id}>
              {/* Scholarship name */}
              <div className="saved-cell saved-cell--name">
                <Link href={`/scheme/${scheme.scheme_id}`} className="saved-scheme-name">
                  {scheme.scheme_name}
                </Link>
                <p className="subtle saved-scheme-benefit">
                  {scheme.benefits.slice(0, 80)}
                  {scheme.benefits.length > 80 ? "…" : ""}
                </p>
              </div>

              {/* Provider */}
              <div className="saved-cell">
                <span className="badge">{scheme.provider}</span>
              </div>

              {/* Deadline */}
              <div className="saved-cell">
                {scheme.deadline ? (
                  <span
                    className={`saved-deadline ${
                      days !== null && days <= 7
                        ? "saved-deadline--critical"
                        : days !== null && days <= 30
                          ? "saved-deadline--warning"
                          : ""
                    }`}
                  >
                    {new Date(scheme.deadline).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                    {days !== null && days >= 0 && (
                      <span className="saved-days-left"> ({days}d left)</span>
                    )}
                  </span>
                ) : (
                  <span className="subtle">—</span>
                )}
              </div>

              {/* Status */}
              <div className="saved-cell">
                <span className={`status-badge ${status.cls}`}>{status.label}</span>
              </div>

              {/* Actions */}
              <div className="saved-cell saved-cell--actions">
                <Link className="button primary" href={`/scheme/${scheme.scheme_id}`}>
                  View
                </Link>
                <button
                  type="button"
                  className="button ghost"
                  onClick={() => handleUnsave(scheme.scheme_id)}
                  disabled={removing === scheme.scheme_id}
                  style={{ fontSize: "13px" }}
                >
                  {removing === scheme.scheme_id ? "…" : "✕ Remove"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
