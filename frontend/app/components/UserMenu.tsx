"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "./AuthContext";

/**
 * Shown in the topbar only when the user is logged in.
 * Displays a small avatar-pill and a Logout button.
 */
export function UserMenu() {
  const { isLoggedIn, logout } = useAuth();
  const router = useRouter();

  if (!isLoggedIn) return null;

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <button
      type="button"
      id="logout-btn"
      className="button ghost user-menu-btn"
      onClick={handleLogout}
      aria-label="Logout"
    >
      Logout
    </button>
  );
}
