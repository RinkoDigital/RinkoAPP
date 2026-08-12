import AsyncStorage from "@react-native-async-storage/async-storage";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, setAuthToken } from "../api/client";
import type { Driver, DriverToken } from "../api/types";

type AuthContextValue = {
  driver: Driver | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<void>;
  loginWithApple: (identityToken: string, name?: string | null) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const STORAGE_KEY = "rinko_driver";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [driver, setDriver] = useState<Driver | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((raw) => {
        if (raw) setDriver(JSON.parse(raw) as Driver);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const persist = useCallback(async (result: DriverToken) => {
    await setAuthToken(result.access_token);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(result.driver));
    setDriver(result.driver);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const result = await api.post<DriverToken>("/auth/login", { email, password });
      await persist(result);
    },
    [persist]
  );

  const signup = useCallback(
    async (name: string, email: string, password: string) => {
      const result = await api.post<DriverToken>("/auth/signup", { name, email, password });
      await persist(result);
    },
    [persist]
  );

  const loginWithGoogle = useCallback(
    async (idToken: string) => {
      const result = await api.post<DriverToken>("/auth/oauth/google", { id_token: idToken });
      await persist(result);
    },
    [persist]
  );

  const loginWithApple = useCallback(
    async (identityToken: string, name?: string | null) => {
      const result = await api.post<DriverToken>("/auth/oauth/apple", {
        identity_token: identityToken,
        name: name ?? null,
      });
      await persist(result);
    },
    [persist]
  );

  const logout = useCallback(async () => {
    await setAuthToken(null);
    await AsyncStorage.removeItem(STORAGE_KEY);
    setDriver(null);
  }, []);

  const value = useMemo(
    () => ({
      driver,
      isAuthenticated: driver !== null,
      isLoading,
      login,
      signup,
      loginWithGoogle,
      loginWithApple,
      logout,
    }),
    [driver, isLoading, login, signup, loginWithGoogle, loginWithApple, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
