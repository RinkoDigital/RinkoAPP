const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;

export const isGoogleSignInConfigured = Boolean(GOOGLE_CLIENT_ID);

type GoogleCredentialResponse = { credential: string };

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize(config: {
            client_id: string;
            callback: (response: GoogleCredentialResponse) => void;
          }): void;
          renderButton(container: HTMLElement, options: Record<string, unknown>): void;
        };
      };
    };
  }
}

const SCRIPT_ID = "google-identity-services";
let scriptLoadPromise: Promise<void> | null = null;

function loadGsiScript(): Promise<void> {
  if (scriptLoadPromise) return scriptLoadPromise;
  scriptLoadPromise = new Promise((resolve, reject) => {
    if (document.getElementById(SCRIPT_ID)) {
      resolve();
      return;
    }
    const script = document.createElement("script");
    script.id = SCRIPT_ID;
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Google Sign-In"));
    document.head.appendChild(script);
  });
  return scriptLoadPromise;
}

/** Loads Google's Identity Services script (once) and renders its official
 * Sign-In button into `container`. Calls `onIdToken` with the verified-by-
 * Google credential JWT — the caller forwards it as-is to
 * POST /auth/oauth/google, which verifies it server-side. No-ops if
 * VITE_GOOGLE_CLIENT_ID isn't set — callers should check
 * `isGoogleSignInConfigured` and skip rendering the container entirely in
 * that case. */
export async function renderGoogleButton(
  container: HTMLElement,
  onIdToken: (idToken: string) => void
): Promise<void> {
  if (!GOOGLE_CLIENT_ID) return;
  await loadGsiScript();
  if (!window.google) return;

  window.google.accounts.id.initialize({
    client_id: GOOGLE_CLIENT_ID,
    callback: (response) => onIdToken(response.credential),
  });
  window.google.accounts.id.renderButton(container, {
    theme: "outline",
    size: "large",
    shape: "pill",
    width: container.clientWidth || 320,
    text: "continue_with",
  });
}
