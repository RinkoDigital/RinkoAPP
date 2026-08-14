import { Directory, File, Paths } from "expo-file-system";
import * as Sharing from "expo-sharing";
import { useRouter } from "expo-router";
import { Alert, StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";
import { API_BASE_URL, api, ApiError } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { AppButton, Card, ErrorBanner, Faint, Screen, Title, TopBar } from "../../src/components/ui";
import { unregisterPushToken } from "../../src/native/pushNotifications";
import { colors } from "../../src/theme";
import { useState } from "react";

export default function AccountScreen() {
  const { t } = useTranslation();
  const { driver, logout } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function deleteAccount() {
    setError(null);
    setDeleting(true);
    try {
      await api.del("/account/me");
      await unregisterPushToken();
      await logout();
      router.replace("/auth");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("common.failedToLoad"));
      setDeleting(false);
    }
  }

  function handleDeleteAccount() {
    Alert.alert(t("account.deleteConfirmTitle"), t("account.deleteConfirm"), [
      { text: t("common.cancel"), style: "cancel" },
      { text: t("account.deleteAccount"), style: "destructive", onPress: deleteAccount },
    ]);
  }

  async function handleExportCsv() {
    setError(null);
    setExporting(true);
    try {
      const headers = await api.authHeader();
      const file = await File.downloadFileAsync(
        `${API_BASE_URL}/sessions/export.csv`,
        new Directory(Paths.cache),
        { headers, idempotent: true }
      );
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(file.uri, { mimeType: "text/csv" });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t("account.errors.exportFailed"));
    } finally {
      setExporting(false);
    }
  }

  async function handleLogout() {
    await unregisterPushToken();
    await logout();
    router.replace("/auth");
  }

  return (
    <Screen>
      <TopBar>
        <Title>{t("account.title")}</Title>
      </TopBar>

      {error && <ErrorBanner message={error} />}

      <Card>
        <Text style={styles.name}>{driver?.name}</Text>
        <Faint>{driver?.email}</Faint>
        {driver && !driver.email_verified && (
          <Text style={styles.unverified}>{t("account.emailUnverified")}</Text>
        )}
      </Card>

      <Card>
        <View style={styles.planHeader}>
          <Text style={styles.cardTitle}>{t("account.plan")}</Text>
          <Text style={styles.planPill}>{t("account.free")}</Text>
        </View>
        <Faint style={{ marginTop: 4 }}>{t("account.planDescription")}</Faint>
      </Card>

      <Card>
        <Text style={styles.cardTitle}>{t("account.dataTitle")}</Text>
        <AppButton
          title={t("account.exportCsv")}
          variant="secondary"
          onPress={handleExportCsv}
          loading={exporting}
          style={{ marginTop: 12 }}
        />
      </Card>

      <AppButton title={t("account.logout")} variant="danger" onPress={handleLogout} />
      <AppButton
        title={t("account.deleteAccount")}
        variant="ghost"
        onPress={handleDeleteAccount}
        loading={deleting}
        style={{ marginTop: 10 }}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  name: {
    color: colors.text,
    fontWeight: "700",
    fontSize: 16,
  },
  unverified: {
    color: colors.sakura,
    fontSize: 13,
    marginTop: 6,
  },
  planHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  cardTitle: {
    color: colors.text,
    fontWeight: "700",
    fontSize: 15,
  },
  planPill: {
    color: colors.good,
    backgroundColor: colors.goodBg,
    paddingVertical: 3,
    paddingHorizontal: 10,
    borderRadius: 999,
    fontSize: 11,
    fontWeight: "700",
    overflow: "hidden",
  },
});
