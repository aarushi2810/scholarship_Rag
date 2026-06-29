import { SearchClient } from "./SearchClient";

export default function SearchPage() {
  return (
    <main className="page">
      <div className="panel hero-panel fade-in">
        <div>
          <p className="eyebrow">Scholarship Search</p>
          <h1>Find Your Best Matches</h1>
          <p className="subtle">
            AI-powered semantic search — describe what you need and we&apos;ll rank the best scholarships for your profile.
          </p>
        </div>
      </div>

      <SearchClient />
    </main>
  );
}
