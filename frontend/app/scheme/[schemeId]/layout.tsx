"use client";
import { AuthGuard } from "../../components/AuthGuard";
import { type ReactNode } from "react";

export default function SchemeLayout({ children }: { children: ReactNode }) {
  return <AuthGuard>{children}</AuthGuard>;
}
