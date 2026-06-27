import type { SavedScholarship } from "../../lib/api";

export function DeadlineTracker({ saved }: { saved: SavedScholarship[] }) {
  const upcoming = [...saved].sort(
    (a, b) => (a.deadline_days_left ?? 9999) - (b.deadline_days_left ?? 9999),
  );

  return (
    <section className="panel">
      <h2>Deadline Tracker</h2>
      <div className="stack">
        {upcoming.map((item) => (
          <div className="split-row card" key={item.id}>
            <div>
              <strong>{item.scholarship.scheme_name}</strong>
              <p className="subtle">{item.scholarship.provider}</p>
            </div>
            <span className="deadline">
              {item.deadline_days_left === null ? "No deadline" : `${item.deadline_days_left} days`}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
