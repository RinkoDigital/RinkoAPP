import { useEffect, useState } from "react";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Directory, File, Paths } from "expo-file-system";
import * as Sharing from "expo-sharing";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";
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
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load report"));
  }, [sessionId]);

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
      const message = err instanceof Error ? err.message : "Failed to download";
      setDownloadError(
        message.includes("402")
          ? "Exportação .docx é um recurso ShiftProof Pro. O JSON do relatório continua grátis."
          : message
      );
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
        <ActivityIndicator color={colors.crimsonGlow} />
      </Screen>
    );
  }

  const diff = report.compensation.difference_cents;

  return (
    <Screen>
      <TopBar>
        <Pressable onPress={() => router.back()}>
          <Text style={styles.backLink}>← Voltar</Text>
        </Pressable>
      </TopBar>

      <Card>
        <Text style={styles.reportTitle}>SHIFTPROOF — INDEPENDENT WORK RECORD</Text>
        <Faint style={{ marginTop: 4 }}>{report.report_number}</Faint>

        <Row label="Driver" value={report.driver_name} />
        <Row label="Carrier / Contractor" value={report.carrier_name} />
        <Row label="Service date" value={formatDate(report.service_date)} />
        {report.route_id && <Row label="Route ID" value={report.route_id} />}
      </Card>

      <Card>
        <Text style={styles.cardTitle}>Work Record</Text>
        <Row label="Route started" value={formatTime(report.work_record.route_started)} />
        <Row label="Route completed" value={formatTime(report.work_record.route_completed)} />
        <Row label="Packages assigned" value={report.work_record.packages_assigned} />
        <Row label="Completed" value={report.work_record.packages_completed} />
        <Row label="Exceptions" value={report.work_record.exceptions} />
        <Row label="Distance" value={`${report.work_record.mileage ?? "—"} mi`} />
      </Card>

      <Card>
        <Text style={styles.cardTitle}>Compensation Record</Text>
        <Row label="Agreed rate" value={`${formatCents(report.compensation.agreed_rate_cents)}/pkg`} />
        <Row label="Expected gross" value={formatCents(report.compensation.expected_gross_cents)} />
        <Row label="Payment due" value={formatDate(report.compensation.payment_due_date)} />
        <Row label="Payment status" value={report.compensation.payment_status.toUpperCase()} />
        {report.compensation.payment_received_cents !== null && (
          <Row label="Received" value={formatCents(report.compensation.payment_received_cents)} />
        )}
        {diff !== null && diff !== undefined && (
          <Row
            label="DIFFERENCE"
            value={
              <Text style={{ color: diff < 0 ? colors.bad : colors.good, fontFamily: "monospace" }}>
                {formatCents(diff)}
              </Text>
            }
          />
        )}
      </Card>

      <Card>
        <Text style={styles.cardTitle}>Supporting Records</Text>
        {report.supporting_records.length === 0 && <Faint>Nenhuma evidência anexada.</Faint>}
        {report.supporting_records.map((ev) => (
          <Text key={ev.id} style={styles.supportingRecord}>
            ✓ {ev.kind.replace(/_/g, " ")}
          </Text>
        ))}
      </Card>

      {diff !== null && diff !== undefined && diff !== 0 && (
        <Text style={styles.disclaimer}>
          Isso não transforma automaticamente este relatório em prova conclusiva numa disputa
          legal — autenticidade, contrato e regras probatórias ainda importam — mas cria
          documentação contemporânea muito melhor do que reconstruir uma rota meses depois.
        </Text>
      )}

      {downloadError && <ErrorBanner message={downloadError} />}
      <AppButton
        title="Baixar .docx"
        variant="secondary"
        onPress={handleDownloadDocx}
        loading={downloading}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  backLink: {
    color: colors.crimsonGlow,
  },
  reportTitle: {
    fontFamily: "serif",
    color: colors.crimsonGlow,
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
