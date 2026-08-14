"use client";
import { ReactNode } from "react";
import { AuthProvider } from "./AuthProvider";
export default function AuthGate({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}
