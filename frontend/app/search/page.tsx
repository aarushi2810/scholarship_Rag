import { SearchClient } from "./SearchClient";
import { getSchemes } from "../../lib/api";

export default async function SearchPage() {
  const schemes = await getSchemes();

  return (
    <main className="page">
      <div className="panel hero-panel fade-in">
        <div>
          <p className="eyebrow">Search</p>
          <h1>Find Your Best Matches</h1>
          <p className="subtle">Instantly search curated scholarships by state, category, education, and funding fit.</p>
        </div>
      </div>

      <SearchClient schemes={schemes} />
    </main>
  );
}
