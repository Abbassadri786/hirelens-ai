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
const PUBLIC_ROUTES = ["/", "/login", "/signin", "/signup"];

function isPublicRoute(pathname: string) {
  return PUBLIC_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Prevent duplicate concurrent auth requests.
  const checkingRef = useRef(false);

  const redirectToLogin = useCallback(
    (currentPath: string) => {
      // CHANGE THIS ONLY if your actual page is /signin.
      const loginPath = "/login";

      const next = encodeURIComponent(currentPath || "/");

      router.replace(`${loginPath}?next=${next}`);
    },
    [router],
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

    /*
     * Don't start another auth check while one is already running.
     */
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

        if (!alive) {
          return;
        }

        setUser(current);
      } catch (error: unknown) {
        if (!alive) {
          return;
        }

        const status =
          typeof error === "object" && error !== null && "status" in error
            ? Number((error as { status?: unknown }).status)
            : undefined;

        if (status === 401) {
          setUser(null);

          redirectToLogin(pathname);

          return;
        }
        console.error("Authentication check failed:", error);

        setUser(null);
      } finally {
        if (alive) {
          setLoading(false);
        }

        checkingRef.current = false;
      }
    }

    void checkAuth();

    return () => {
      alive = false;
    };
  }, [pathname, redirectToLogin]);

  const refreshUser = useCallback(async () => {
    // Don't check authentication from public pages.
    if (isPublicRoute(pathname)) {
      setUser(null);
      return null;
    }

    try {
      const current = await api.me();

      setUser(current);

      return current;
    } catch (error: unknown) {
      const status =
        typeof error === "object" && error !== null && "status" in error
          ? Number((error as { status?: unknown }).status)
          : undefined;

      if (status === 401) {
        setUser(null);

        redirectToLogin(pathname);
      } else {
        console.error("refreshUser failed:", error);
      }

      return null;
    }
  }, [pathname, redirectToLogin]);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const value = useContext(AuthContext);

  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return value;
}
