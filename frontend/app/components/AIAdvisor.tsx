"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { ChatWindow } from "./ChatWindow";

const AUTH_ROUTES = ["/login", "/register"];

export function AIAdvisor() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    setIsOpen(false);
  }, [pathname]);

  // Don't show the AI advisor on auth pages
  if (AUTH_ROUTES.some((route) => pathname.startsWith(route))) {
    return null;
  }

  return (
    <>
      {/* Floating Action Button (FAB) Panel */}
      <aside className="assistant-fab" aria-label="AI Advisor">
        <div className="assistant-row">
          <div className="assistant-icon">AI</div>
          <div>
            <strong>AI Scholarship Advisor</strong>
            <p>Ask questions about eligibility, deadlines, funding, and applications.</p>
          </div>
        </div>
        <button
          className="button primary"
          type="button"
          onClick={() => setIsOpen(true)}
        >
          Ask a Question
        </button>
      </aside>

      {/* Slide-over Drawer Portal */}
      {isOpen && (
        <>
          <div className="drawer-overlay" onClick={() => setIsOpen(false)} />
          <div className="drawer" role="dialog" aria-modal="true" aria-label="AI Scholarship Advisor Chat">
            <div className="drawer-header">
              <h2>AI Scholarship Advisor</h2>
              <button
                className="drawer-close"
                type="button"
                onClick={() => setIsOpen(false)}
                aria-label="Close chat"
              >
                ✕
              </button>
            </div>
            <ChatWindow />
          </div>
        </>
      )}
    </>
  );
}


