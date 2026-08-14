"use client";

import { ReactNode, createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { authApi } from "@/api/auth";
import { ApiError } from "@/api/client";
import type { User } from "@/types/domain";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  refreshUser: () => Promise<User | null>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const PUBLIC_ROUTES = ["/", "/login", "/signin", "/signup", "/jobs"];

function isPublicRoute(pathname: string) {
  return PUBLIC_ROUTES.some((route) => route === "/" ? pathname === "/" : pathname === route || pathname.startsWith(`${route}/`));
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const checking = useRef(false);

  const redirectToLogin = useCallback(() => {
    const next = pathname || "/dashboard";
    router.replace(`/login?next=${encodeURIComponent(next)}`);
  }, [pathname, router]);

  useEffect(() => {
    let alive = true;
    if (isPublicRoute(pathname)) {
      setLoading(false);
      return () => { alive = false; };
    }
    if (checking.current) return () => { alive = false; };
    checking.current = true;
    setLoading(true);

    void authApi.me()
      .then((current) => {
        if (alive) setUser(current);
      })
      .catch((error) => {
        if (!alive) return;
        if (error instanceof ApiError && error.status === 401) {
          setUser(null);
          redirectToLogin();
        } else {
          console.error("Auth check failed:", error);
          setUser(null);
        }
      })
      .finally(() => {
        if (alive) setLoading(false);
        checking.current = false;
      });

    return () => { alive = false; };
  }, [pathname, redirectToLogin]);

  const refreshUser = useCallback(async () => {
    try {
      const current = await authApi.me();
      setUser(current);
      return current;
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setUser(null);
        redirectToLogin();
      }
      return null;
    }
  }, [redirectToLogin]);

  const signOut = useCallback(async () => {
    try {
      await authApi.logout();
    } catch (error) {
      // The local auth state must still be cleared if the server session is already gone.
      console.warn("Sign out request failed; clearing local auth state.", error);
    } finally {
      setUser(null);
      router.replace("/login");
      router.refresh();
    }
  }, [router]);

  return <AuthContext.Provider value={{ user, loading, refreshUser, signOut }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
