import { useCallback, useState } from "react";
import { useFocusEffect, useRouter } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { ActivityIndicator } from "react-native";
import { api, ApiError } from "../../src/api/client";
import { formatCents, formatDate } from "../../src/api/format";
import type { LedgerSummary, WorkSession } from "../../src/api/types";
import { useAuth } from "../../src/auth/AuthContext";
import { StatusPill } from "../../src/components/StatusPill";
import { Card, EmptyState, ErrorBanner, Faint, Mono, Screen, TopBar } from "../../src/components/ui";
import { colors } from "../../src/theme";

export default function HomeScreen() {
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
        .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load"));
    }, [])
  );

  const firstName = driver?.name.split(" ")[0] ?? "";

  return (
    <View style={styles.container}>
      <Screen>
        <TopBar>
          <Text style={styles.greeting}>Boa tarde, {firstName}</Text>
        </TopBar>

        {error && <ErrorBanner message={error} />}

        <Card style={styles.ledgerCard}>
          <Faint>OUTSTANDING EARNINGS</Faint>
          {ledger ? (
            <Mono style={styles.ledgerAmount}>{formatCents(ledger.outstanding_total_cents)}</Mono>
          ) : (
            <ActivityIndicator color={colors.crimsonGlow} style={{ marginVertical: 8 }} />
          )}
          <Pressable onPress={() => router.push("/(tabs)/ledger")}>
            <Text style={styles.ledgerLink}>Ver payment ledger →</Text>
          </Pressable>
        </Card>

        <Text style={styles.sectionTitle}>Sessões recentes</Text>

        {sessions === null && <ActivityIndicator color={colors.crimsonGlow} />}
        {sessions !== null && sessions.length === 0 && (
          <EmptyState>Nenhuma work session ainda. Toque em + para começar.</EmptyState>
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
                {formatDate(s.service_date)} · {s.packages_completed}/{s.packages_assigned} pacotes
              </Faint>
              <Mono style={{ marginTop: 6 }}>{formatCents(s.expected_gross_cents)}</Mono>
            </Card>
          </Pressable>
        ))}
      </Screen>

      <Pressable style={styles.fab} onPress={() => router.push("/sessions/new")}>
        <Text style={styles.fabText}>+</Text>
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
    color: colors.crimsonGlow,
    marginTop: 4,
    marginBottom: 8,
  },
  ledgerLink: {
    color: colors.crimsonGlow,
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
    bottom: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.crimson,
    alignItems: "center",
    justifyContent: "center",
  },
  fabText: {
    color: colors.accentInk,
    fontSize: 28,
    lineHeight: 30,
  },
});
