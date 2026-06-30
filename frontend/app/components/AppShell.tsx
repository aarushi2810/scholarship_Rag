"use client";

/**
 * Client-side shell — handles dynamic import of AIAdvisor with ssr:false.
 * Must be a client component because `next/dynamic` with `ssr: false` is
 * not allowed in Server Components.
 */
import dynamic from "next/dynamic";
import type { ReactNode } from "react";

const AIAdvisor = dynamic(
  () => import("./AIAdvisor").then((mod) => ({ default: mod.AIAdvisor })),
  {
    ssr: false,
    loading: () => null, // no placeholder — FAB appears after hydration
  },
);

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      {children}
      {/* AIAdvisor is lazy-loaded — does not block initial page render */}
      <AIAdvisor />
    </>
  );
}
