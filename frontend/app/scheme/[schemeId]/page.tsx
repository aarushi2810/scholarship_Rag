import Link from "next/link";
import { SaveButton } from "../../components/SaveButton";
import { formatIncome, getScheme, supportLabel } from "../../../lib/api";

export default async function SchemeDetailPage({ params }: { params: Promise<{ schemeId: string }> }) {
  const { schemeId } = await params;
  const scheme = await getScheme(schemeId);

  return (
    <main className="page">
      <div className="panel hero-panel fade-in">
        <div>
          <p className="eyebrow">{scheme.provider}</p>
          <h1>{scheme.scheme_name}</h1>
          <p className="subtle">{scheme.state} · {scheme.education_levels.join(", ")}</p>
        </div>
        <div className="actions">
          <span className="badge emerald">Verified Source</span>
          <span className="badge cyan">{supportLabel(scheme)}</span>
          <SaveButton schemeId={scheme.scheme_id} />
          <a className="button primary" href={scheme.source_url} target="_blank" rel="noreferrer">
            Official Link
          </a>
        </div>
      </div>

      <div className="detail-grid">
        <section className="panel">
          <h2>Overview</h2>
          <p>{scheme.benefits}</p>
          <div className="pill-row">
            {scheme.categories.map((category) => (
              <span className="pill" key={category}>{category}</span>
            ))}
            <span className="pill">{formatIncome(scheme.income_ceiling)}</span>
          </div>
        </section>

        <section className="panel">
          <h2>Eligibility Checklist</h2>
          <p>{scheme.eligibility_text}</p>
          <ul className="plain-list">
            <li>✓ Income limit: {formatIncome(scheme.income_ceiling)}</li>
            <li>✓ Categories: {scheme.categories.join(", ")}</li>
            <li>✓ Education: {scheme.education_levels.join(", ")}</li>
            <li>✓ Source: official {scheme.provider} portal</li>
          </ul>
        </section>

        <section className="panel">
          <h2>Documents Required</h2>
          <ul className="plain-list">
            {scheme.documents_required.map((document) => (
              <li key={document}>{document}</li>
            ))}
          </ul>
        </section>

        <section className="panel">
          <h2>Application Timeline</h2>
          <ol className="timeline">
            <li>Review eligibility and income/category requirements.</li>
            <li>Collect documents and academic records.</li>
            <li>Submit application through the official portal.</li>
            <li>Track institutional verification and deadline status.</li>
          </ol>
        </section>

        <section className="panel">
          <h2>Application Process</h2>
          <p>{scheme.application_process}</p>
          <div className="actions">
            <Link className="button" href="/dashboard">Back to Dashboard</Link>
            <Link className="button" href="/search">Search More</Link>
          </div>
        </section>

        <section className="panel">
          <h2>Related Paths</h2>
          <div className="pill-row">
            <Link className="pill" href="/search?education=UG">UG Scholarships</Link>
            <Link className="pill" href="/search?state=Punjab">Punjab Schemes</Link>
            <Link className="pill" href="/search?category=General">General Category</Link>
          </div>
        </section>
      </div>
    </main>
  );
}
