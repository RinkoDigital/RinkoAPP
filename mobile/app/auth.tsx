import { useState } from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { Redirect, useRouter } from "expo-router";
import { ApiError } from "../src/api/client";
import { useAuth } from "../src/auth/AuthContext";
import { AppButton, ErrorBanner, Field, LoadingScreen, Screen } from "../src/components/ui";
import { colors } from "../src/theme";

const kitsuneMask = require("../assets/kitsune-mask.webp");

export default function AuthScreen() {
  const { isAuthenticated, isLoading: authLoading, login, signup } = useAuth();
  const router = useRouter();

  const [mode, setMode] = useState<"login" | "signup">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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

  return (
    <Screen>
      <View style={styles.hero}>
        <Image source={kitsuneMask} style={styles.mask} resizeMode="contain" />
        <Text style={styles.wordmark}>RINKO</Text>
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
  mask: {
    width: 180,
    height: 198,
    marginBottom: -8,
  },
  wordmark: {
    fontFamily: "serif",
    fontSize: 32,
    letterSpacing: 6,
    color: colors.crimsonGlow,
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
    backgroundColor: colors.crimson,
    width: "100%",
    marginTop: 10,
    position: "absolute",
    bottom: -1,
  },
});
