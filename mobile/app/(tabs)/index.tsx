import { useCallback, useState } from "react";
import { useFocusEffect, useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { ActivityIndicator } from "react-native";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "../../src/api/client";
import { formatCents, formatDate } from "../../src/api/format";
import type { LedgerSummary, WorkSession } from "../../src/api/types";
import { useAuth } from "../../src/auth/AuthContext";
import { StatusPill } from "../../src/components/StatusPill";
import { Card, EmptyState, ErrorBanner, Faint, Mono, Screen, TopBar } from "../../src/components/ui";
import { colors } from "../../src/theme";

export default function HomeScreen() {
  const { t } = useTranslation();
  const { driver } = useAuth();
  const router = useRouter();
  const [ledger, setLedger] = useState<LedgerSummary | null>(null);
  const [sessions, setSessions] = useState<WorkSession[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      Promise.all([api.get<LedgerSummary>("/ledger"), api.get<WorkSession[]>("/sessions")])
        .then(([ledgerData, sessionsData]) => {
          setLedger(ledgerData);
          setSessions(sessionsData);
        })
        .catch((err) => setError(err instanceof ApiError ? err.message : t("common.failedToLoad")));
    }, [t])
  );

  const firstName = driver?.name.split(" ")[0] ?? "";

  return (
    <View style={styles.container}>
      <Screen>
        <TopBar>
          <Text style={styles.greeting}>{t("home.greeting", { name: firstName })}</Text>
        </TopBar>

        {error && <ErrorBanner message={error} />}

        <Card style={styles.ledgerCard}>
          <Faint>{t("home.outstandingEarnings")}</Faint>
          {ledger ? (
            <Mono style={styles.ledgerAmount}>{formatCents(ledger.outstanding_total_cents)}</Mono>
          ) : (
            <ActivityIndicator color={colors.violetGlow} style={{ marginVertical: 8 }} />
          )}
          <Pressable onPress={() => router.push("/(tabs)/ledger")}>
            <Text style={styles.ledgerLink}>{t("home.viewPaymentLedger")}</Text>
          </Pressable>
        </Card>

        <Text style={styles.sectionTitle}>{t("home.recentSessions")}</Text>

        {sessions === null && <ActivityIndicator color={colors.violetGlow} />}
        {sessions !== null && sessions.length === 0 && (
          <EmptyState>{t("home.noSessionsYet")}</EmptyState>
        )}
        {sessions?.map((s) => (
          <Pressable key={s.id} onPress={() => router.push(`/sessions/${s.id}`)}>
            <Card>
              <View style={styles.rowBetween}>
                <Text style={styles.sessionCarrier}>
                  {s.carrier_name}
                  {s.route_id ? <Text style={{ color: colors.textFaint }}> · {s.route_id}</Text> : null}
                </Text>
                <StatusPill status={s.status === "open" ? "pending" : s.payment_status} />
              </View>
              <Faint style={{ marginTop: 4 }}>
                {t("home.sessionMeta", {
                  date: formatDate(s.service_date),
                  completed: s.packages_completed,
                  assigned: s.packages_assigned,
                })}
              </Faint>
              <Mono style={{ marginTop: 6 }}>{formatCents(s.expected_gross_cents)}</Mono>
            </Card>
          </Pressable>
        ))}
      </Screen>

      <Pressable
        style={styles.fab}
        onPress={() => router.push("/sessions/new")}
        accessibilityLabel={t("home.startSessionAria")}
      >
        <Ionicons name="add" size={30} color={colors.accentInk} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  greeting: {
    fontFamily: "serif",
    fontSize: 18,
    color: colors.text,
  },
  ledgerCard: {
    backgroundColor: colors.surface2,
  },
  ledgerAmount: {
    fontSize: 32,
    color: colors.violetGlow,
    marginTop: 4,
    marginBottom: 8,
  },
  ledgerLink: {
    color: colors.violetGlow,
    fontSize: 13,
  },
  sectionTitle: {
    color: colors.text,
    fontWeight: "700",
    fontSize: 16,
    marginTop: 8,
    marginBottom: 8,
  },
  rowBetween: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  sessionCarrier: {
    color: colors.text,
    fontWeight: "700",
  },
  fab: {
    position: "absolute",
    right: 20,
    bottom: 32,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.violet,
    alignItems: "center",
    justifyContent: "center",
  },
});
