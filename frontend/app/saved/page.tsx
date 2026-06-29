import { getSavedScholarships } from "../../lib/api";
import { SavedClient } from "./SavedClient";

export default async function SavedPage() {
  const saved = await getSavedScholarships();

  return (
    <main className="page">
      <div className="panel hero-panel fade-in">
        <div>
          <p className="eyebrow">Your Library</p>
          <h1>Saved Scholarships</h1>
          <p className="subtle">
            {saved.length > 0
              ? `${saved.length} scholarship${saved.length === 1 ? "" : "s"} saved — track deadlines and apply on time.`
              : "Save scholarships you want to apply for and track them here."}
          </p>
        </div>
      </div>

      <SavedClient initialSaved={saved} />
    </main>
  );
}
