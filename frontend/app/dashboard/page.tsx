import Link from "next/link";
import { DeadlineAlerts } from "../components/DeadlineAlerts";
import { ProfileCompletion } from "../components/ProfileCompletion";
import { RecommendationCard } from "../components/RecommendationCard";
import { getDashboard, getSchemes } from "../../lib/api";

export default async function DashboardPage() {
  const [dashboard, allSchemes] = await Promise.all([getDashboard(), getSchemes()]);

  const eligibleCount = allSchemes.length;
  const closingSoon = dashboard.saved_scholarships.filter(
    (item) => item.deadline_days_left !== null && item.deadline_days_left <= 30,
  ).length;
  const avgMatch =
    dashboard.top_matches.length > 0
      ? Math.round(
          dashboard.top_matches.reduce((sum, m) => sum + m.match_score, 0) /
            dashboard.top_matches.length,
        )
      : null;

  // Extract first name for greeting
  const firstName = dashboard.name.split(" ")[0];

  // Profile fields for the completion widget
  const profileFields = {
    category: dashboard.category,
    income: dashboard.income,
    education_level: dashboard.education_level,
    state: dashboard.state,
    degree: dashboard.degree,
    cgpa: dashboard.cgpa,
    gender: dashboard.gender,
  };

  const savedSchemeIds = new Set(
    dashboard.saved_scholarships.map((s) => s.scholarship.scheme_id),
  );

  return (
    <main className="page">
      {/* ── Deadline Alerts ─────────────────────────────────────────── */}
      <DeadlineAlerts saved={dashboard.saved_scholarships} />

      {/* ── Hero Panel ──────────────────────────────────────────────── */}
      <div className="panel hero-panel fade-in" style={{ marginBottom: "18px" }}>
        <p className="eyebrow">Welcome back</p>
        <h1>Hello, {firstName} 👋</h1>
        {dashboard.state || dashboard.education_level || dashboard.category ? (
          <p className="subtle">
            Based on your{" "}
            {[dashboard.state, dashboard.education_level, dashboard.category]
              .filter(Boolean)
              .join(" · ")}{" "}
            profile
          </p>
        ) : (
          <p className="subtle">
            Complete your profile to unlock personalised matches.
          </p>
        )}
      </div>

      {/* ── Stats Row ───────────────────────────────────────────────── */}
      <section className="stats-grid">
        <div className="stat-card fade-in">
          <p className="stat-label">Available Scholarships</p>
          <p className="stat-value">{eligibleCount}</p>
        </div>
        <div className="stat-card fade-in">
          <p className="stat-label">Saved</p>
          <p className="stat-value">{dashboard.saved_scholarships.length}</p>
        </div>
        <div className="stat-card fade-in">
          <p className="stat-label">Closing Soon</p>
          <p className="stat-value stat-value--urgent">{closingSoon}</p>
        </div>
        <div className="stat-card fade-in">
          <p className="stat-label">Average Match</p>
          <p className="stat-value stat-value--match">
            {avgMatch !== null ? `${avgMatch}%` : "—"}
          </p>
        </div>
      </section>

      <div className="grid">
        {/* ── Sidebar ─────────────────────────────────────────────── */}
        <aside className="stack">
          {/* Profile Completion */}
          <ProfileCompletion
            completion={dashboard.profile_completion}
            profile={profileFields}
          />

          {/* Saved Scholarships */}
          <section className="panel">
            <div className="inline-head">
              <h2>Saved</h2>
              <Link className="button ghost" href="/saved">
                View all →
              </Link>
            </div>
            {dashboard.saved_scholarships.length === 0 ? (
              <p className="subtle" style={{ margin: 0 }}>
                No saved scholarships yet.{" "}
                <Link href="/search" style={{ color: "var(--indigo)" }}>
                  Search now
                </Link>
              </p>
            ) : (
              <div className="stack">
                {dashboard.saved_scholarships.slice(0, 4).map((item) => (
                  <Link
                    className="card"
                    href={`/scheme/${item.scholarship.scheme_id}`}
                    key={item.id}
                  >
                    <div className="split-row">
                      <div>
                        <h3 style={{ marginBottom: "2px" }}>
                          {item.scholarship.scheme_name}
                        </h3>
                        <p className="subtle" style={{ margin: 0, fontSize: "13px" }}>
                          {item.scholarship.provider}
                        </p>
                      </div>
                      <span
                        className={`deadline ${
                          item.deadline_days_left !== null &&
                          item.deadline_days_left <= 7
                            ? "deadline--critical"
                            : ""
                        }`}
                      >
                        {item.deadline_days_left === null
                          ? "No deadline"
                          : item.deadline_days_left < 0
                            ? "Closed"
                            : `${item.deadline_days_left}d left`}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </section>
        </aside>

        {/* ── Top Matches ─────────────────────────────────────────── */}
        <section className="stack">
          <div className="panel">
            <div className="inline-head">
              <div>
                <h2>Recommended for You</h2>
                <p className="subtle">
                  Ranked by eligibility, education fit, and deadline urgency.
                </p>
              </div>
              <Link className="button primary" href="/search">
                Explore All
              </Link>
            </div>
          </div>

          {dashboard.top_matches.length === 0 ? (
            <div className="panel">
              <p className="subtle">
                No matches yet.{" "}
                <Link href="/profile" style={{ color: "var(--indigo)" }}>
                  Complete your profile
                </Link>{" "}
                to get personalised recommendations.
              </p>
            </div>
          ) : (
            dashboard.top_matches.map((item, index) => (
              <RecommendationCard
                item={item}
                rank={index + 1}
                isSavedInitial={savedSchemeIds.has(item.scholarship.scheme_id)}
                key={item.scholarship.scheme_id}
              />
            ))
          )}
        </section>
      </div>
    </main>
  );
}
