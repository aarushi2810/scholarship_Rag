"use client";

import { useState } from "react";
import { saveScholarship, unsaveScholarship } from "../../lib/api";

export function SaveButton({
  schemeId,
  isSavedInitial = false,
}: {
  schemeId: string;
  isSavedInitial?: boolean;
}) {
  const [isSaved, setIsSaved] = useState(isSavedInitial);
  const [loading, setLoading] = useState(false);

  async function handleToggle() {
    if (loading) return;
    setLoading(true);
    try {
      if (isSaved) {
        const ok = await unsaveScholarship(schemeId);
        if (ok) setIsSaved(false);
      } else {
        const item = await saveScholarship(schemeId);
        if (item) setIsSaved(true);
      }
    } catch {
      // silently ignore
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      className={`button ${isSaved ? "emerald" : "ghost"}`}
      type="button"
      onClick={handleToggle}
      disabled={loading}
      aria-pressed={isSaved}
      aria-label={isSaved ? "Unsave scholarship" : "Save scholarship"}
    >
      {loading ? "…" : isSaved ? "★ Saved" : "☆ Save"}
    </button>
  );
}
