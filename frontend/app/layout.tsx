import type { Metadata } from "next";
import Link from "next/link";
import { AppShell } from "./components/AppShell";
import { AuthProvider } from "./components/AuthContext";
import { UserMenu } from "./components/UserMenu";
import "./globals.css";

export const metadata: Metadata = {
  title: "ScholarMatch AI",
  description: "AI-powered scholarship discovery and recommendations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <div className="shell">
            <header className="topbar">
              <Link className="brand" href="/dashboard">
                <span className="brand-mark">SM</span>
                <span>ScholarMatch AI</span>
              </Link>
              <nav className="nav" aria-label="Primary navigation">
                <Link href="/dashboard">Dashboard</Link>
                <Link href="/search">Search</Link>
                <Link href="/saved">Saved</Link>
                <UserMenu />
              </nav>
            </header>
            {/*
             * AppShell is a client component that lazy-loads AIAdvisor (ssr:false).
             * This keeps RootLayout as a Server Component while still deferring
             * the chat bundle from the critical render path.
             */}
            <AppShell>{children}</AppShell>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
