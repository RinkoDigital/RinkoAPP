import AsyncStorage from "@react-native-async-storage/async-storage";
import Constants from "expo-constants";

const API_BASE_URL: string =
  (Constants.expoConfig?.extra?.apiBaseUrl as string | undefined) ??
  process.env.EXPO_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

const TOKEN_KEY = "rinko_token";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

let authToken: string | null = null;
let tokenLoaded = false;
let tokenLoadPromise: Promise<void> | null = null;

async function ensureTokenLoaded() {
  if (tokenLoaded) return;
  if (!tokenLoadPromise) {
    tokenLoadPromise = AsyncStorage.getItem(TOKEN_KEY).then((stored) => {
      authToken = stored;
      tokenLoaded = true;
    });
  }
  await tokenLoadPromise;
}

export async function setAuthToken(token: string | null) {
  authToken = token;
  tokenLoaded = true;
  if (token) {
    await AsyncStorage.setItem(TOKEN_KEY, token);
  } else {
    await AsyncStorage.removeItem(TOKEN_KEY);
  }
}

export function getAuthToken() {
  return authToken;
}

export { ensureTokenLoaded };

type RequestOptions = {
  method?: string;
  body?: unknown;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  await ensureTokenLoaded();

  const headers: Record<string, string> = {};
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  let body: BodyInit | undefined;
  if (options.body instanceof FormData) {
    body = options.body;
  } else if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.body);
  }

  const resp = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body,
  });

  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const data = await resp.json();
      detail = data.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(resp.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  if (resp.status === 204 || resp.status === 202) {
    return undefined as T;
  }

  const contentType = resp.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await resp.json()) as T;
  }
  return (await resp.blob()) as unknown as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body }),
  del: <T>(path: string, body?: unknown) => request<T>(path, { method: "DELETE", body }),
  postForm: <T>(path: string, form: FormData) =>
    request<T>(path, { method: "POST", body: form }),
  downloadUrl: (path: string) => (/^https?:\/\//.test(path) ? path : `${API_BASE_URL}${path}`),
  authHeader: async (): Promise<Record<string, string>> => {
    await ensureTokenLoaded();
    const headers: Record<string, string> = {};
    if (authToken) headers.Authorization = `Bearer ${authToken}`;
    return headers;
  },
};

export { API_BASE_URL };
