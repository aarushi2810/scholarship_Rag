"use client";

import { useEffect, useState, type CSSProperties } from "react";
import type { Scholarship } from "../../lib/api";

const FIXED_STEPS = [
  "Fill online application form",
  "Submit for institute verification",
  "Track status on official portal",
];

type ChecklistItem = {
  id: string;
  label: string;
  checked: boolean;
};

function storageKey(schemeId: string) {
  return `checklist_${schemeId}`;
}

function buildItems(scheme: Scholarship): ChecklistItem[] {
  const docItems: ChecklistItem[] = scheme.documents_required.map((doc, i) => ({
    id: `doc_${i}`,
    label: doc,
    checked: false,
  }));
  const stepItems: ChecklistItem[] = FIXED_STEPS.map((step, i) => ({
    id: `step_${i}`,
    label: step,
    checked: false,
  }));
  return [...docItems, ...stepItems];
}

function loadItems(scheme: Scholarship): ChecklistItem[] {
  const base = buildItems(scheme);
  if (typeof window === "undefined") return base;
  try {
    const stored = localStorage.getItem(storageKey(scheme.scheme_id));
    if (!stored) return base;
    const savedChecked: Record<string, boolean> = JSON.parse(stored);
    return base.map((item) => ({
      ...item,
      checked: savedChecked[item.id] ?? false,
    }));
  } catch {
    return base;
  }
}

function saveItems(schemeId: string, items: ChecklistItem[]) {
  const map: Record<string, boolean> = {};
  items.forEach((item) => {
    map[item.id] = item.checked;
  });
  localStorage.setItem(storageKey(schemeId), JSON.stringify(map));
}

export function ApplicationChecklist({ scheme }: { scheme: Scholarship }) {
  const [items, setItems] = useState<ChecklistItem[]>(() => buildItems(scheme));
  const [mounted, setMounted] = useState(false);

  // Load from localStorage after hydration
  useEffect(() => {
    setItems(loadItems(scheme));
    setMounted(true);
  }, [scheme.scheme_id]);

  function toggle(id: string) {
    setItems((prev) => {
      const next = prev.map((item) =>
        item.id === id ? { ...item, checked: !item.checked } : item,
      );
      saveItems(scheme.scheme_id, next);
      return next;
    });
  }

  function resetAll() {
    const reset = items.map((item) => ({ ...item, checked: false }));
    setItems(reset);
    saveItems(scheme.scheme_id, reset);
  }

  const completed = items.filter((i) => i.checked).length;
  const total = items.length;
  const percent = total > 0 ? Math.round((completed / total) * 100) : 0;

  const docItems = items.filter((i) => i.id.startsWith("doc_"));
  const stepItems = items.filter((i) => i.id.startsWith("step_"));

  return (
    <section className="panel checklist-panel">
      <div className="checklist-header">
        <div>
          <h2>Application Checklist</h2>
          <p className="subtle">
            {completed === total && total > 0
              ? "All done — you're ready to apply! 🎉"
              : `${completed} of ${total} tasks completed`}
          </p>
        </div>
        {/* Progress ring */}
        <div
          className="ring checklist-ring"
          style={{ "--value": percent } as CSSProperties}
          aria-label={`${percent}% complete`}
        >
          {percent}%
        </div>
      </div>

      {/* Progress bar */}
      <div className="progress" style={{ marginBottom: "20px" }}>
        <span style={{ width: `${percent}%` }} />
      </div>

      {/* Documents section */}
      {docItems.length > 0 && (
        <>
          <p className="checklist-section-label">Documents Required</p>
          <ul className="checklist-list">
            {docItems.map((item) => (
              <li
                key={item.id}
                className={`checklist-item ${item.checked ? "checklist-item--done" : ""}`}
              >
                <label className="checklist-label">
                  <input
                    type="checkbox"
                    checked={mounted ? item.checked : false}
                    onChange={() => toggle(item.id)}
                    className="checklist-checkbox"
                  />
                  <span className="checklist-text">{item.label}</span>
                </label>
              </li>
            ))}
          </ul>
        </>
      )}

      {/* Steps section */}
      <p className="checklist-section-label" style={{ marginTop: "16px" }}>
        Application Steps
      </p>
      <ul className="checklist-list">
        {stepItems.map((item) => (
          <li
            key={item.id}
            className={`checklist-item ${item.checked ? "checklist-item--done" : ""}`}
          >
            <label className="checklist-label">
              <input
                type="checkbox"
                checked={mounted ? item.checked : false}
                onChange={() => toggle(item.id)}
                className="checklist-checkbox"
              />
              <span className="checklist-text">{item.label}</span>
            </label>
          </li>
        ))}
      </ul>

      {completed > 0 && (
        <button
          type="button"
          className="button ghost checklist-reset"
          onClick={resetAll}
          style={{ marginTop: "16px", fontSize: "13px" }}
        >
          Reset checklist
        </button>
      )}
    </section>
  );
}
