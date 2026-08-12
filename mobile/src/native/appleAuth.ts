import { Platform } from "react-native";
import * as AppleAuthentication from "expo-apple-authentication";

export type AppleSignInResult = {
  identityToken: string;
  /** Apple only ever hands this over once, in the client SDK result on the
   * very first authorization — never inside the token itself. */
  fullName: string | null;
};

/** "Sign in with Apple" only exists on iOS (it's an Apple Developer
 * capability, not a web/Android SDK) — callers should hide the button
 * entirely elsewhere. */
export const isAppleSignInAvailable = Platform.OS === "ios";

export async function signInWithApple(): Promise<AppleSignInResult | null> {
  try {
    const credential = await AppleAuthentication.signInAsync({
      requestedScopes: [
        AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
        AppleAuthentication.AppleAuthenticationScope.EMAIL,
      ],
    });
    if (!credential.identityToken) return null;
    const fullName = credential.fullName
      ? [credential.fullName.givenName, credential.fullName.familyName].filter(Boolean).join(" ")
      : null;
    return { identityToken: credential.identityToken, fullName: fullName || null };
  } catch (err: any) {
    if (err?.code === "ERR_REQUEST_CANCELED") return null;
    throw err;
  }
}
