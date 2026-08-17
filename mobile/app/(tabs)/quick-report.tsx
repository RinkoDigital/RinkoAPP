import { useCallback, useMemo, useState } from "react";
import { useFocusEffect, useRouter } from "expo-router";
import { FlatList, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useTranslation } from "react-i18next";
import { Card, EmptyState, Faint, Screen, Title, TopBar } from "../../src/components/ui";
import { getQuickReports, type QuickReport, type QuickReportStatus } from "../../src/quickReports";
import { colors, radii } from "../../src/theme";

const FILTERS: { value: "ALL" | QuickReportStatus; labelKey: string }[] = [
  { value: "ALL", labelKey: "quickReport.history.filters.all" },
  { value: "COMPLETE", labelKey: "quickReport.history.filters.complete" },
  { value: "PARTIAL", labelKey: "quickReport.history.filters.partial" },
  { value: "ATTENTION", labelKey: "quickReport.history.filters.attention" },
];

const STATUS_COLOR: Record<QuickReportStatus, { bg: string; fg: string }> = {
  COMPLETE: { bg: colors.goodBg, fg: colors.good },
  PARTIAL: { bg: colors.pendingBg, fg: colors.pending },
  ATTENTION: { bg: colors.badBg, fg: colors.bad },
};

export default function QuickReportListScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const [reports, setReports] = useState<QuickReport[]>([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"ALL" | QuickReportStatus>("ALL");

  useFocusEffect(
    useCallback(() => {
      getQuickReports().then(setReports);
    }, [])
  );

  const filteredReports = useMemo(() => {
    const query = search.trim().toLowerCase();
    return reports.filter((report) => {
      const matchesSearch =
        !query ||
        report.id.toLowerCase().includes(query) ||
        report.company.toLowerCase().includes(query) ||
        report.driver.toLowerCase().includes(query) ||
        report.route.toLowerCase().includes(query);
      const matchesFilter = filter === "ALL" || report.status === filter;
      return matchesSearch && matchesFilter;
    });
  }, [reports, search, filter]);

  const stats = useMemo(() => {
    const totalBoxes = reports.reduce((sum, r) => sum + r.total, 0);
    const delivered = reports.reduce((sum, r) => sum + r.delivered, 0);
    return {
      reports: reports.length,
      totalBoxes,
      delivered,
      completion: totalBoxes > 0 ? ((delivered / totalBoxes) * 100).toFixed(1) : "0.0",
    };
  }, [reports]);

  return (
    <Screen scroll={false}>
      <TopBar>
        <Title>{t("quickReport.history.title")}</Title>
        <Pressable style={styles.newButton} onPress={() => router.push("/quick-report/new")}>
          <Text style={styles.newButtonText}>{t("quickReport.history.newReport")}</Text>
        </Pressable>
      </TopBar>

      <View style={styles.body}>
        <Faint>{t("quickReport.history.subtitle")}</Faint>

        <View style={styles.statsRow}>
          <StatCard label={t("quickReport.history.statsReports")} value={String(stats.reports)} />
          <StatCard label={t("quickReport.history.statsBoxes")} value={String(stats.totalBoxes)} />
          <StatCard label={t("quickReport.history.statsDelivered")} value={String(stats.delivered)} />
          <StatCard label={t("quickReport.history.statsRate")} value={`${stats.completion}%`} />
        </View>

        <TextInput
          value={search}
          onChangeText={setSearch}
          placeholder={t("quickReport.history.searchPlaceholder")}
          placeholderTextColor={colors.textFaint}
          style={styles.search}
        />

        <View style={styles.filters}>
          {FILTERS.map((f) => (
            <Pressable
              key={f.value}
              onPress={() => setFilter(f.value)}
              style={[styles.filterChip, filter === f.value && styles.filterChipActive]}
            >
              <Text style={[styles.filterText, filter === f.value && styles.filterTextActive]}>
                {t(f.labelKey)}
              </Text>
            </Pressable>
          ))}
        </View>

        <FlatList
          data={filteredReports}
          keyExtractor={(item) => item.id}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingBottom: 90 }}
          ListEmptyComponent={
            <EmptyState>
              {t("quickReport.history.emptyTitle")}
              {"\n"}
              {t("quickReport.history.emptyText")}
            </EmptyState>
          }
          renderItem={({ item }) => (
            <Pressable onPress={() => router.push(`/quick-report/${item.id}`)}>
              <Card>
                <View style={styles.rowBetween}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.company}>{item.company}</Text>
                    <Faint style={{ marginTop: 2 }}>{item.driver}</Faint>
                  </View>
                  <View style={[styles.statusPill, { backgroundColor: STATUS_COLOR[item.status].bg }]}>
                    <Text style={[styles.statusText, { color: STATUS_COLOR[item.status].fg }]}>
                      {item.status}
                    </Text>
                  </View>
                </View>
                <View style={[styles.rowBetween, { marginTop: 10 }]}>
                  <Faint style={{ fontSize: 12 }}>{item.date}</Faint>
                  <Faint style={{ fontSize: 12 }}>{item.id}</Faint>
                </View>
                <View style={styles.metrics}>
                  <Metric label={t("quickReport.form.total")} value={item.total} />
                  <Metric label={t("quickReport.form.delivered")} value={item.delivered} color={colors.violetGlow} />
                  <Metric label={t("quickReport.form.notDelivered")} value={item.notDelivered} color={colors.bad} />
                  <Metric label={t("quickReport.history.statsRate")} value={`${item.rate.toFixed(1)}%`} />
                </View>
                <Faint style={{ marginTop: 10 }}>{item.route}</Faint>
              </Card>
            </Pressable>
          )}
        />
      </View>
    </Screen>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.statCard}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function Metric({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <View style={{ flex: 1 }}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={[styles.metricValue, color ? { color } : null]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  body: {
    flex: 1,
    paddingHorizontal: 20,
  },
  newButton: {
    backgroundColor: colors.violet,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: radii.input,
  },
  newButtonText: {
    color: colors.accentInk,
    fontSize: 11,
    fontWeight: "800",
  },
  statsRow: {
    flexDirection: "row",
    gap: 8,
    marginTop: 14,
    marginBottom: 14,
  },
  statCard: {
    flex: 1,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radii.card,
    padding: 10,
  },
  statValue: {
    color: colors.text,
    fontSize: 16,
    fontWeight: "800",
  },
  statLabel: {
    color: colors.textFaint,
    fontSize: 8,
    marginTop: 3,
  },
  search: {
    backgroundColor: colors.cardSunken,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radii.input,
    color: colors.text,
    fontSize: 13,
    paddingHorizontal: 13,
    paddingVertical: 11,
  },
  filters: {
    flexDirection: "row",
    gap: 7,
    marginVertical: 12,
    flexWrap: "wrap",
  },
  filterChip: {
    paddingHorizontal: 11,
    paddingVertical: 7,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.line,
  },
  filterChipActive: {
    borderColor: colors.violet,
    backgroundColor: colors.surface2,
  },
  filterText: {
    color: colors.textFaint,
    fontSize: 11,
    fontWeight: "700",
  },
  filterTextActive: {
    color: colors.violetGlow,
  },
  rowBetween: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  company: {
    color: colors.text,
    fontWeight: "700",
    fontSize: 15,
  },
  statusPill: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: radii.pill,
  },
  statusText: {
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  metrics: {
    flexDirection: "row",
    gap: 10,
    marginTop: 10,
  },
  metricLabel: {
    color: colors.textFaint,
    fontSize: 9,
  },
  metricValue: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700",
    marginTop: 2,
  },
});
