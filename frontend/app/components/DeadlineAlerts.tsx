"use client";

import { useState } from "react";
import Link from "next/link";
import type { SavedScholarship } from "../../lib/api";

function getAlertLevel(days: number): "critical" | "warning" | null {
  if (days <= 7) return "critical";
  if (days <= 14) return "warning";
  return null;
}

function getDismissedKey(schemeId: string) {
  return `deadline_dismissed_${schemeId}`;
}

export function DeadlineAlerts({ saved }: { saved: SavedScholarship[] }) {
  const urgent = saved.filter((item) => {
    const days = item.deadline_days_left;
    if (days === null || days < 0) return false;
    return days <= 14;
  });

  const [dismissed, setDismissed] = useState<Set<string>>(() => {
    if (typeof window === "undefined") return new Set();
    const keys = urgent.map((s) => s.scholarship.scheme_id);
    const dismissedKeys = keys.filter((id) =>
      localStorage.getItem(getDismissedKey(id)) === "true",
    );
    return new Set(dismissedKeys);
  });

  const visible = urgent.filter(
    (item) => !dismissed.has(item.scholarship.scheme_id),
  );

  if (visible.length === 0) return null;

  function dismiss(schemeId: string) {
    localStorage.setItem(getDismissedKey(schemeId), "true");
    setDismissed((prev) => new Set([...prev, schemeId]));
  }

  return (
    <div className="deadline-alerts-stack" role="alert" aria-live="polite">
      {visible.map((item) => {
        const days = item.deadline_days_left!;
        const level = getAlertLevel(days);
        const scheme = item.scholarship;

        return (
          <div
            key={scheme.scheme_id}
            className={`deadline-alert deadline-alert--${level}`}
          >
            <div className="deadline-alert__inner">
              <span className="deadline-alert__icon">
                {level === "critical" ? "🔴" : "⚠️"}
              </span>
              <div className="deadline-alert__body">
                <Link
                  href={`/scheme/${scheme.scheme_id}`}
                  className="deadline-alert__name"
                >
                  {scheme.scheme_name}
                </Link>
                <span className="deadline-alert__days">
                  {days === 0
                    ? "Closes today!"
                    : days === 1
                      ? "Closes tomorrow"
                      : `Ends in ${days} days`}
                </span>
              </div>
            </div>
            <button
              type="button"
              className="deadline-alert__dismiss"
              aria-label="Dismiss alert"
              onClick={() => dismiss(scheme.scheme_id)}
            >
              ✕
            </button>
          </div>
        );
      })}
    </div>
  );
}
