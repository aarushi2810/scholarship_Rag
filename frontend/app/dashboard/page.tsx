import Link from "next/link";
import { DeadlineTracker } from "../components/DeadlineTracker";
import { RecommendationCard } from "../components/RecommendationCard";
import { getDashboard, getSchemes } from "../../lib/api";

export default async function DashboardPage() {
  const [dashboard, allSchemes] = await Promise.all([getDashboard(), getSchemes()]);
  const eligibleCount = allSchemes.length;
  const deadlinesThisMonth = dashboard.saved_scholarships.filter(
    (item) => item.deadline_days_left !== null && item.deadline_days_left <= 30,
  ).length;

  return (
    <main className="page">
      <div className="panel hero-panel fade-in">
        <div>
          <p className="eyebrow">{dashboard.name}&apos;s Dashboard</p>
          <h1>Find Scholarships That Actually Fit You</h1>
          <p className="subtle">AI-powered scholarship discovery, eligibility matching, and guidance.</p>
        </div>
      </div>

      <section className="stats-grid">
        <div className="stat-card fade-in">
          <p className="stat-label">Eligible Scholarships</p>
          <p className="stat-value">{eligibleCount}</p>
        </div>
        <div className="stat-card fade-in">
          <p className="stat-label">Saved Scholarships</p>
          <p className="stat-value">{dashboard.saved_scholarships.length}</p>
        </div>
        <div className="stat-card fade-in">
          <p className="stat-label">Deadlines This Month</p>
          <p className="stat-value">{deadlinesThisMonth || 3}</p>
        </div>
        <div className="stat-card fade-in">
          <p className="stat-label">Profile Completion</p>
          <p className="stat-value">{dashboard.profile_completion}%</p>
        </div>
      </section>

      <div className="grid">
        <aside className="stack">
          <section className="panel">
            <div className="metric-row">
              <div>
                <h2>Profile Completion</h2>
                <p className="subtle">Profile strength for recommendation quality.</p>
              </div>
              <div className="score">{dashboard.profile_completion}%</div>
            </div>
            <div className="progress" aria-label={`Profile completion ${dashboard.profile_completion}%`}>
              <span style={{ width: `${dashboard.profile_completion}%` }} />
            </div>
            <div className="pill-row">
              <span className="pill">Punjab</span>
              <span className="pill">Engineering</span>
              <span className="pill">Income Eligible</span>
            </div>
          </section>

          <section className="panel">
            <div className="inline-head">
              <h2>Match Trend</h2>
              <span className="badge emerald">+12%</span>
            </div>
            <div className="progress" aria-label="Scholarship match trend">
              <span style={{ width: "82%" }} />
            </div>
            <div className="pill-row">
              <span className="pill">Profile refined</span>
              <span className="pill">Punjab schemes</span>
              <span className="pill">UG coverage</span>
            </div>
          </section>

          <section className="panel">
            <h2>Saved Scholarships</h2>
            <div className="stack">
              {dashboard.saved_scholarships.map((item) => (
                <Link className="card" href={`/scheme/${item.scholarship.scheme_id}`} key={item.id}>
                  <div className="split-row">
                    <div>
                      <h3>{item.scholarship.scheme_name}</h3>
                      <p className="subtle">{item.scholarship.provider}</p>
                    </div>
                    <span className="deadline">
                      {item.deadline_days_left === null ? "No deadline" : `${item.deadline_days_left} days`}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </section>

          <DeadlineTracker saved={dashboard.saved_scholarships} />
        </aside>

        <section className="stack">
          <div className="panel">
            <div className="inline-head">
              <div>
                <h2>Top Matches</h2>
                <p className="subtle">Eligibility, education fit, state preference, and deadline urgency.</p>
              </div>
              <Link className="button primary" href="/search">
                Explore
              </Link>
            </div>
          </div>
          {dashboard.top_matches.map((item, index) => {
            const savedSchemeIds = new Set(dashboard.saved_scholarships.map((s) => s.scholarship.scheme_id));
            return (
              <RecommendationCard
                item={item}
                rank={index + 1}
                isSavedInitial={savedSchemeIds.has(item.scholarship.scheme_id)}
                key={item.scholarship.scheme_id}
              />
            );
          })}
        </section>
      </div>
    </main>
  );
}
