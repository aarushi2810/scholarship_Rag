import type { Metadata } from "next";
import Link from "next/link";
import { AIAdvisor } from "./components/AIAdvisor";
import "./globals.css";

export const metadata: Metadata = {
  title: "ScholarshipRAG",
  description: "AI-powered scholarship discovery and recommendation platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="topbar">
            <Link className="brand" href="/dashboard">
              <span className="brand-mark">SR</span>
              <span>ScholarshipRAG</span>
            </Link>
            <nav className="nav" aria-label="Primary navigation">
              <Link href="/dashboard">Dashboard</Link>
              <Link href="/search">Search</Link>
              <Link href="/scheme/nsp_merit_punjab">Scheme Detail</Link>
            </nav>
          </header>
          {children}
          <AIAdvisor />
        </div>
      </body>
    </html>
  );
}
