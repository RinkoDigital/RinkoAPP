import * as WebBrowser from "expo-web-browser";
import { ResponseType } from "expo-auth-session";
import { useIdTokenAuthRequest } from "expo-auth-session/providers/google";

// Required once per app so the browser tab opened by promptAsync() closes
// itself and hands control back to the app after Google redirects.
WebBrowser.maybeCompleteAuthSession();

const GOOGLE_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID;

export const isGoogleSignInConfigured = Boolean(GOOGLE_CLIENT_ID);

/** Wraps expo-auth-session's Google ID-token flow behind a single hook.
 *
 * We only have one OAuth client — a "Web application" client (no package
 * name/SHA-1 needed, unlike the "Android" client type) — so `clientId` is
 * used on every platform. That client type has no secret we could safely
 * embed in the app anyway, which is why `responseType` is forced to
 * `IdToken`: it's Google's implicit flow (the token comes back straight in
 * the redirect, no code-for-token exchange step that would need one).
 *
 * Returns null for `signIn()` when no client id is configured — callers
 * should hide the "Continuar com Google" button in that case (check
 * `isGoogleSignInConfigured`) rather than let the user tap into a broken
 * flow. The hook itself always runs with *some* clientId — even a
 * placeholder — because `useIdTokenAuthRequest` throws synchronously
 * during render if given `undefined`, and hooks can't be called
 * conditionally; `signIn()` just never reaches `promptAsync()` in that
 * case, so the placeholder is never actually used. */
export function useGoogleIdToken() {
  const [request, , promptAsync] = useIdTokenAuthRequest({
    clientId: GOOGLE_CLIENT_ID ?? "not-configured",
    responseType: ResponseType.IdToken,
  });

  async function signIn(): Promise<string | null> {
    if (!GOOGLE_CLIENT_ID || !request) return null;
    const result = await promptAsync();
    if (result.type !== "success") return null;
    return result.params.id_token ?? null;
  }

  return { signIn, isReady: Boolean(request) && isGoogleSignInConfigured };
}
