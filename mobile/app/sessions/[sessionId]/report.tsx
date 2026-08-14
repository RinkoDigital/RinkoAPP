import { useEffect, useState } from "react";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Directory, File, Paths } from "expo-file-system";
import * as Sharing from "expo-sharing";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";
import { API_BASE_URL, api, ApiError } from "../../../src/api/client";
import { formatCents, formatDate, formatTime } from "../../../src/api/format";
import type { WorkReport } from "../../../src/api/types";
import {
  AppButton,
  Card,
  ErrorBanner,
  Faint,
  Row,
  Screen,
  TopBar,
} from "../../../src/components/ui";
import { colors } from "../../../src/theme";

export default function WorkReportScreen() {
  const { t } = useTranslation();
  const { sessionId } = useLocalSearchParams<{ sessionId: string }>();
  const router = useRouter();
  const [report, setReport] = useState<WorkReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    api
      .get<WorkReport>(`/sessions/${sessionId}/work-report`)
      .then(setReport)
      .catch((err) => setError(err instanceof ApiError ? err.message : t("workReport.errors.loadFailed")));
  }, [sessionId, t]);

  async function handleDownloadDocx() {
    if (!sessionId) return;
    setDownloadError(null);
    setDownloading(true);
    try {
      const headers = await api.authHeader();
      const file = await File.downloadFileAsync(
        `${API_BASE_URL}/sessions/${sessionId}/work-report.docx`,
        new Directory(Paths.cache),
        { headers, idempotent: true }
      );
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(file.uri);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : t("workReport.errors.downloadFailed");
      setDownloadError(message.includes("402") ? t("workReport.errors.proFeature") : message);
    } finally {
      setDownloading(false);
    }
  }

  if (error) {
    return (
      <Screen>
        <ErrorBanner message={error} />
      </Screen>
    );
  }

  if (!report) {
    return (
      <Screen>
        <ActivityIndicator color={colors.violetGlow} />
      </Screen>
    );
  }

  const diff = report.compensation.difference_cents;

  return (
    <Screen>
      <TopBar>
        <Pressable onPress={() => router.back()}>
          <Text style={styles.backLink}>{t("workReport.back")}</Text>
        </Pressable>
      </TopBar>

      <Card>
        <Text style={styles.reportTitle}>{t("workReport.title")}</Text>
        <Faint style={{ marginTop: 4 }}>{report.report_number}</Faint>

        <Row label={t("workReport.driver")} value={report.driver_name} />
        <Row label={t("workReport.carrier")} value={report.carrier_name} />
        <Row label={t("workReport.serviceDate")} value={formatDate(report.service_date)} />
        {report.route_id && <Row label={t("workReport.routeId")} value={report.route_id} />}
      </Card>

      <Card>
        <Text style={styles.cardTitle}>{t("workReport.workRecord.title")}</Text>
        <Row label={t("workReport.workRecord.routeStarted")} value={formatTime(report.work_record.route_started)} />
        <Row label={t("workReport.workRecord.routeCompleted")} value={formatTime(report.work_record.route_completed)} />
        <Row label={t("workReport.workRecord.packagesAssigned")} value={report.work_record.packages_assigned} />
        <Row label={t("workReport.workRecord.completed")} value={report.work_record.packages_completed} />
        <Row label={t("workReport.workRecord.exceptions")} value={report.work_record.exceptions} />
        <Row label={t("workReport.workRecord.distance")} value={`${report.work_record.mileage ?? "—"} mi`} />
      </Card>

      <Card>
        <Text style={styles.cardTitle}>{t("workReport.compensation.title")}</Text>
        <Row label={t("workReport.compensation.agreedRate")} value={`${formatCents(report.compensation.agreed_rate_cents)}/pkg`} />
        <Row label={t("workReport.compensation.expectedGross")} value={formatCents(report.compensation.expected_gross_cents)} />
        <Row label={t("workReport.compensation.paymentDue")} value={formatDate(report.compensation.payment_due_date)} />
        <Row label={t("workReport.compensation.paymentStatus")} value={report.compensation.payment_status.toUpperCase()} />
        {report.compensation.payment_received_cents !== null && (
          <Row label={t("workReport.compensation.received")} value={formatCents(report.compensation.payment_received_cents)} />
        )}
        {diff !== null && diff !== undefined && (
          <Row
            label={t("workReport.compensation.difference")}
            value={
              <Text style={{ color: diff < 0 ? colors.bad : colors.good, fontFamily: "monospace" }}>
                {formatCents(diff)}
              </Text>
            }
          />
        )}
      </Card>

      <Card>
        <Text style={styles.cardTitle}>{t("workReport.supportingRecords.title")}</Text>
        {report.supporting_records.length === 0 && <Faint>{t("workReport.supportingRecords.none")}</Faint>}
        {report.supporting_records.map((ev) => (
          <Text key={ev.id} style={styles.supportingRecord}>
            ✓ {ev.kind.replace(/_/g, " ")}
          </Text>
        ))}
      </Card>

      {diff !== null && diff !== undefined && diff !== 0 && (
        <Text style={styles.disclaimer}>{t("workReport.disclaimer")}</Text>
      )}

      {downloadError && <ErrorBanner message={downloadError} />}
      <AppButton
        title={t("workReport.downloadDocx")}
        variant="secondary"
        onPress={handleDownloadDocx}
        loading={downloading}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  backLink: {
    color: colors.violetGlow,
  },
  reportTitle: {
    fontFamily: "serif",
    color: colors.violetGlow,
    fontSize: 14,
  },
  cardTitle: {
    color: colors.text,
    fontWeight: "700",
    fontSize: 15,
    marginBottom: 4,
  },
  supportingRecord: {
    color: colors.text,
    paddingVertical: 6,
  },
  disclaimer: {
    color: colors.textFaint,
    fontStyle: "italic",
    fontSize: 12,
    marginBottom: 14,
    lineHeight: 18,
  },
});
