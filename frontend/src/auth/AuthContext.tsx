import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { api, setAuthToken } from "../api/client";
import type { Driver, DriverToken } from "../api/types";

type AuthContextValue = {
  driver: Driver | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshDriver: (driver: Driver) => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const STORAGE_KEY = "rinko_driver";

function loadStoredDriver(): Driver | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Driver;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [driver, setDriver] = useState<Driver | null>(loadStoredDriver);

  const persist = useCallback((result: DriverToken) => {
    setAuthToken(result.access_token);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(result.driver));
    setDriver(result.driver);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const result = await api.post<DriverToken>("/auth/login", { email, password });
      persist(result);
    },
    [persist]
  );

  const signup = useCallback(
    async (name: string, email: string, password: string) => {
      const result = await api.post<DriverToken>("/auth/signup", { name, email, password });
      persist(result);
    },
    [persist]
  );

  const logout = useCallback(() => {
    setAuthToken(null);
    localStorage.removeItem(STORAGE_KEY);
    setDriver(null);
  }, []);

  const refreshDriver = useCallback((updated: Driver) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    setDriver(updated);
  }, []);

  const value = useMemo(
    () => ({ driver, isAuthenticated: driver !== null, login, signup, logout, refreshDriver }),
    [driver, login, signup, logout, refreshDriver]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
