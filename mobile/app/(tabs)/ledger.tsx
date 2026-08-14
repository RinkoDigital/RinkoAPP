import { useCallback, useState } from "react";
import { useFocusEffect, useRouter } from "expo-router";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "../../src/api/client";
import { formatCents, formatDate } from "../../src/api/format";
import type { LedgerSummary } from "../../src/api/types";
import { StatusPill } from "../../src/components/StatusPill";
import { Card, EmptyState, ErrorBanner, Faint, Mono, Row, Screen, TopBar, Title } from "../../src/components/ui";
import { colors } from "../../src/theme";

export default function LedgerScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const [ledger, setLedger] = useState<LedgerSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      api
        .get<LedgerSummary>("/ledger")
        .then(setLedger)
        .catch((err) => setError(err instanceof ApiError ? err.message : t("common.failedToLoad")));
    }, [t])
  );

  return (
    <Screen>
      <TopBar>
        <Title>{t("ledger.title")}</Title>
      </TopBar>

      {error && <ErrorBanner message={error} />}

      <Card style={styles.summaryCard}>
        <Faint>{t("ledger.outstanding")}</Faint>
        {ledger ? (
          <Mono style={styles.amount}>{formatCents(ledger.outstanding_total_cents)}</Mono>
        ) : (
          <ActivityIndicator color={colors.violetGlow} style={{ marginTop: 8 }} />
        )}
      </Card>

      {ledger?.entries.length === 0 && <EmptyState>{t("ledger.none")}</EmptyState>}

      {ledger?.entries.map((entry) => (
        <Pressable key={entry.session_id} onPress={() => router.push(`/sessions/${entry.session_id}`)}>
          <Card>
            <View style={styles.rowBetween}>
              <Text style={styles.carrier}>{entry.carrier_name}</Text>
              <StatusPill status={entry.payment_status} />
            </View>
            <Faint>
              {formatDate(entry.service_date)}
              {entry.route_id ? ` · ${entry.route_id}` : ""}
            </Faint>
            <Row label={t("ledger.expected")} value={formatCents(entry.expected_gross_cents)} />
            <Row label={t("ledger.outstandingRow")} value={formatCents(entry.outstanding_cents)} />
          </Card>
        </Pressable>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  summaryCard: {
    backgroundColor: colors.surface2,
    alignItems: "center",
  },
  amount: {
    fontSize: 32,
    color: colors.violetGlow,
    marginTop: 4,
  },
  rowBetween: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  carrier: {
    color: colors.text,
    fontWeight: "700",
  },
});
