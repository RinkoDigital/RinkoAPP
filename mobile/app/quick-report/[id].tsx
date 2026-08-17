import { useCallback, useState } from "react";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import * as Print from "expo-print";
import * as Sharing from "expo-sharing";
import { ActivityIndicator, Alert, Pressable, StyleSheet, Text } from "react-native";
import { useTranslation } from "react-i18next";
import { AppButton, Card, ErrorBanner, Screen, TopBar } from "../../src/components/ui";
import { QuickReportPreview } from "../../src/components/QuickReportPreview";
import { buildQuickReportHtml } from "../../src/quickReportPdf";
import { deleteQuickReport, getQuickReport, type QuickReport } from "../../src/quickReports";
import { colors } from "../../src/theme";

export default function QuickReportDetailScreen() {
  const { t } = useTranslation();
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [report, setReport] = useState<QuickReport | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      if (!id) return;
      getQuickReport(id).then((found) => {
        setReport(found);
        setLoaded(true);
      });
    }, [id])
  );

  async function downloadPdf() {
    if (!report) return;
    setBusy(true);
    setError(null);
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

  function handleDelete() {
    if (!report) return;
    Alert.alert(t("quickReport.detail.deleteConfirmTitle"), t("quickReport.detail.deleteConfirm"), [
      { text: t("common.cancel"), style: "cancel" },
      {
        text: t("quickReport.history.delete"),
        style: "destructive",
        onPress: async () => {
          await deleteQuickReport(report.id);
          router.back();
        },
      },
    ]);
  }

  return (
    <Screen>
      <TopBar>
        <Pressable onPress={() => router.back()}>
          <Text style={styles.backLink}>{t("quickReport.detail.back")}</Text>
        </Pressable>
      </TopBar>

      {error && <ErrorBanner message={error} />}

      {!loaded && <ActivityIndicator color={colors.violetGlow} />}
      {loaded && !report && (
        <Card>
          <Text style={styles.notFound}>{t("quickReport.detail.notFound")}</Text>
        </Card>
      )}

      {report && (
        <>
          <QuickReportPreview report={report} />
          <AppButton
            title={busy ? t("quickReport.form.preparingPdf") : t("quickReport.form.downloadPdf")}
            variant="secondary"
            onPress={downloadPdf}
            loading={busy}
            style={{ marginTop: 14 }}
          />
          <AppButton
            title={t("quickReport.history.delete")}
            variant="danger"
            onPress={handleDelete}
            style={{ marginTop: 10 }}
          />
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  backLink: {
    color: colors.violetGlow,
  },
  notFound: {
    color: colors.textFaint,
    textAlign: "center",
    paddingVertical: 20,
  },
});
