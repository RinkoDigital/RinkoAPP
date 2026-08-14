import { useState } from "react";
import { Image, Linking, Pressable, StyleSheet, Text, View } from "react-native";
import { Redirect, useRouter } from "expo-router";
import * as AppleAuthentication from "expo-apple-authentication";
import { ApiError } from "../src/api/client";
import { useAuth } from "../src/auth/AuthContext";
import { AppButton, ErrorBanner, Field, LoadingScreen, Screen } from "../src/components/ui";
import { isAppleSignInAvailable, signInWithApple } from "../src/native/appleAuth";
import { isGoogleSignInConfigured, useGoogleIdToken } from "../src/native/googleAuth";
import { colors } from "../src/theme";

const authLogo = require("../assets/auth-logo.png");

export default function AuthScreen() {
  const { isAuthenticated, isLoading: authLoading, login, signup, loginWithGoogle, loginWithApple } =
    useAuth();
  const router = useRouter();
  const { signIn: signInWithGoogle, isReady: googleReady } = useGoogleIdToken();

  const [mode, setMode] = useState<"login" | "signup">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(false);

  if (authLoading) return <LoadingScreen />;
  if (isAuthenticated) return <Redirect href="/" />;

  async function handleSubmit() {
    setError(null);
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await signup(name, email, password);
      }
      router.replace("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleSignIn() {
    setError(null);
    setOauthLoading(true);
    try {
      const idToken = await signInWithGoogle();
      if (!idToken) return; // user canceled — nothing to report
      await loginWithGoogle(idToken);
      router.replace("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to sign in with Google");
    } finally {
      setOauthLoading(false);
    }
  }

  async function handleAppleSignIn() {
    setError(null);
    setOauthLoading(true);
    try {
      const result = await signInWithApple();
      if (!result) return; // user canceled — nothing to report
      await loginWithApple(result.identityToken, result.fullName);
      router.replace("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to sign in with Apple");
    } finally {
      setOauthLoading(false);
    }
  }

  return (
    <Screen>
      <View style={styles.hero}>
        <Image source={authLogo} style={styles.logo} resizeMode="contain" />
        <Text style={styles.tagline}>Your routes. Your work. Your records.</Text>
      </View>

      <View style={styles.card}>
        <View style={styles.tabs}>
          <Pressable onPress={() => setMode("login")} style={styles.tabBtn}>
            <Text style={[styles.tabText, mode === "login" && styles.tabTextActive]}>Entrar</Text>
            {mode === "login" && <View style={styles.tabUnderline} />}
          </Pressable>
          <Pressable onPress={() => setMode("signup")} style={styles.tabBtn}>
            <Text style={[styles.tabText, mode === "signup" && styles.tabTextActive]}>
              Criar conta
            </Text>
            {mode === "signup" && <View style={styles.tabUnderline} />}
          </Pressable>
        </View>

        {error && <ErrorBanner message={error} />}

        {mode === "signup" && (
          <Field label="Nome" value={name} onChangeText={setName} autoCapitalize="words" />
        )}
        <Field
          label="Email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
        />
        <Field label="Senha" value={password} onChangeText={setPassword} secureTextEntry />

        <AppButton
          title={mode === "login" ? "Entrar" : "Criar conta"}
          onPress={handleSubmit}
          loading={loading}
        />

        {(googleReady || isAppleSignInAvailable) && (
          <>
            <View style={styles.divider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>ou continue com</Text>
              <View style={styles.dividerLine} />
            </View>

            {isGoogleSignInConfigured && (
              <AppButton
                title="Continuar com Google"
                variant="secondary"
                onPress={handleGoogleSignIn}
                loading={oauthLoading}
                disabled={!googleReady}
              />
            )}

            {isAppleSignInAvailable && (
              <AppleAuthentication.AppleAuthenticationButton
                buttonType={AppleAuthentication.AppleAuthenticationButtonType.CONTINUE}
                buttonStyle={AppleAuthentication.AppleAuthenticationButtonStyle.WHITE}
                cornerRadius={10}
                style={styles.appleButton}
                onPress={handleAppleSignIn}
              />
            )}
          </>
        )}

        <Pressable
          onPress={() => Linking.openURL("https://shiftprooff.netlify.app/privacy.html")}
          style={{ alignItems: "center", marginTop: 18 }}
        >
          <Text style={styles.privacyLink}>Política de Privacidade</Text>
        </Pressable>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: {
    alignItems: "center",
    marginTop: 40,
    marginBottom: 32,
  },
  logo: {
    width: 260,
    height: 182,
  },
  tagline: {
    color: colors.textMuted,
    letterSpacing: 0.5,
    marginTop: 4,
  },
  card: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 14,
    padding: 18,
  },
  tabs: {
    flexDirection: "row",
    marginBottom: 18,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
  },
  tabBtn: {
    flex: 1,
    alignItems: "center",
    paddingBottom: 10,
  },
  tabText: {
    color: colors.textFaint,
    fontWeight: "600",
  },
  tabTextActive: {
    color: colors.text,
  },
  tabUnderline: {
    height: 2,
    backgroundColor: colors.violet,
    width: "100%",
    marginTop: 10,
    position: "absolute",
    bottom: -1,
  },
  divider: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 18,
    marginBottom: 14,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: colors.line,
  },
  dividerText: {
    color: colors.textFaint,
    fontSize: 12,
    marginHorizontal: 10,
  },
  appleButton: {
    height: 46,
    marginTop: 10,
  },
  privacyLink: {
    color: colors.textFaint,
    fontSize: 12,
  },
});
