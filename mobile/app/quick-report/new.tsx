import { useState } from "react";
import { useRouter } from "expo-router";
import * as Print from "expo-print";
import * as Sharing from "expo-sharing";
import { Pressable, StyleSheet, Text } from "react-native";
import { useTranslation } from "react-i18next";
import { AppButton, Card, ErrorBanner, Field, Screen, Title, TopBar } from "../../src/components/ui";
import { QuickReportPreview } from "../../src/components/QuickReportPreview";
import { buildQuickReportHtml } from "../../src/quickReportPdf";
import {
  formatQuickReportDate,
  nextQuickReportId,
  quickReportStatus,
  saveQuickReport,
  type QuickReport,
} from "../../src/quickReports";
import { colors } from "../../src/theme";

export default function NewQuickReportScreen() {
  const { t } = useTranslation();
  const router = useRouter();

  const [company, setCompany] = useState("");
  const [driver, setDriver] = useState("");
  const [total, setTotal] = useState("");
  const [delivered, setDelivered] = useState("");
  const [notDelivered, setNotDelivered] = useState("");
  const [route, setRoute] = useState("");
  const [notes, setNotes] = useState("");
  const [report, setReport] = useState<QuickReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function generateReport() {
    setError(null);
    const t_ = Number(total);
    const d = Number(delivered);
    const nd = Number(notDelivered);

    if (!company.trim() || !driver.trim()) {
      setError(t("quickReport.errors.missingFields"));
      return;
    }
    if (![t_, d, nd].every(Number.isInteger)) {
      setError(t("quickReport.errors.wholeNumbers"));
      return;
    }
    if ([t_, d, nd].some((n) => n < 0)) {
      setError(t("quickReport.errors.negative"));
      return;
    }
    if (d + nd !== t_) {
      setError(t("quickReport.errors.mismatch", { delivered: d, notDelivered: nd, total: t_ }));
      return;
    }

    const rate = t_ === 0 ? 0 : (d / t_) * 100;
    const id = await nextQuickReportId();

    const newReport: QuickReport = {
      id,
      company: company.trim(),
      driver: driver.trim(),
      total: t_,
      delivered: d,
      notDelivered: nd,
      route: route.trim() || t("quickReport.history.noRoute"),
      notes: notes.trim() || "—",
      rate,
      date: formatQuickReportDate(),
      status: quickReportStatus(rate),
    };

    try {
      await saveQuickReport(newReport);
      setReport(newReport);
    } catch {
      setError(t("quickReport.errors.saveFailed"));
    }
  }

  async function downloadPdf() {
    if (!report) return;
    setBusy(true);
    try {
      const { uri } = await Print.printToFileAsync({
        html: buildQuickReportHtml(report),
        width: 612,
        height: 792,
      });
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(uri, { mimeType: "application/pdf" });
      }
    } catch {
      setError(t("quickReport.errors.pdfFailed"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen>
      <TopBar>
        <Pressable onPress={() => router.back()}>
          <Text style={styles.backLink}>{t("quickReport.detail.back")}</Text>
        </Pressable>
      </TopBar>

      <Title>{t("quickReport.form.title")}</Title>

      <Card>
        <Field
          label={t("quickReport.form.company")}
          placeholder={t("quickReport.form.companyPlaceholder")}
          value={company}
          onChangeText={setCompany}
        />
        <Field
          label={t("quickReport.form.driver")}
          placeholder={t("quickReport.form.driverPlaceholder")}
          value={driver}
          onChangeText={setDriver}
        />
        <Field
          label={t("quickReport.form.total")}
          placeholder="100"
          value={total}
          onChangeText={setTotal}
          keyboardType="number-pad"
        />
        <Field
          label={t("quickReport.form.delivered")}
          placeholder="96"
          value={delivered}
          onChangeText={setDelivered}
          keyboardType="number-pad"
        />
        <Field
          label={t("quickReport.form.notDelivered")}
          placeholder="4"
          value={notDelivered}
          onChangeText={setNotDelivered}
          keyboardType="number-pad"
        />
        <Field
          label={t("quickReport.form.route")}
          placeholder={t("quickReport.form.routePlaceholder")}
          value={route}
          onChangeText={setRoute}
        />
        <Field
          label={t("quickReport.form.notes")}
          placeholder={t("quickReport.form.notesPlaceholder")}
          value={notes}
          onChangeText={setNotes}
          multiline
          numberOfLines={3}
        />

        {error && <ErrorBanner message={error} />}

        <AppButton title={t("quickReport.form.generate")} onPress={generateReport} />
        {report && (
          <AppButton
            title={busy ? t("quickReport.form.preparingPdf") : t("quickReport.form.downloadPdf")}
            variant="secondary"
            onPress={downloadPdf}
            loading={busy}
            style={{ marginTop: 10 }}
          />
        )}
      </Card>

      {report ? (
        <QuickReportPreview report={report} />
      ) : (
        <Card>
          <Text style={styles.previewHint}>{t("quickReport.form.previewHint")}</Text>
        </Card>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  backLink: {
    color: colors.violetGlow,
  },
  previewHint: {
    color: colors.textFaint,
    textAlign: "center",
    paddingVertical: 40,
  },
});
