"use client";

import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { usePathname, useRouter } from "next/navigation";
import { api, User } from "@/lib/api";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  refreshUser: () => Promise<User | null>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const PUBLIC_ROUTES = ["/login", "/signin", "/signup"];

function isPublicRoute(pathname: string) {
  return PUBLIC_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`)
  );
}

function getStatus(error: unknown): number | undefined {
  if (typeof error === "object" && error !== null && "status" in error) {
    const value = (error as { status?: unknown }).status;
    return typeof value === "number" ? value : undefined;
  }
  return undefined;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const checkingRef = useRef(false);

  const redirectToLogin = useCallback(
    (currentPath: string) => {
      const loginPath = "/login";
      router.replace(
        `${loginPath}?next=${encodeURIComponent(currentPath || "/")}`
      );
    },
    [router]
  );

  useEffect(() => {
    let alive = true;

    if (isPublicRoute(pathname)) {
      setUser(null);
      setLoading(false);
      return () => {
        alive = false;
      };
    }

    if (checkingRef.current) {
      return () => {
        alive = false;
      };
    }

    checkingRef.current = true;
    setLoading(true);

    async function checkAuth() {
      try {
        const current = await api.me();
        if (alive) setUser(current);
      } catch (error) {
        if (!alive) return;

        const status = getStatus(error);

        if (status === 401) {
          setUser(null);
          redirectToLogin(pathname);
        } else {
          console.error("Auth check failed:", error);
          setUser(null);
        }
      } finally {
        if (alive) setLoading(false);
        checkingRef.current = false;
      }
    }

    void checkAuth();

    return () => {
      alive = false;
    };
  }, [pathname, redirectToLogin]);

  const refreshUser = useCallback(async () => {
    if (isPublicRoute(pathname)) {
      setUser(null);
      return null;
    }

    try {
      const current = await api.me();
      setUser(current);
      return current;
    } catch (error) {
      if (getStatus(error) === 401) {
        setUser(null);
        redirectToLogin(pathname);
      } else {
        console.error("refreshUser failed:", error);
      }
      return null;
    }
  }, [pathname, redirectToLogin]);

  return (
    <AuthContext.Provider value={{ user, loading, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
