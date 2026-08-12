import { Directory, File, Paths } from "expo-file-system";
import * as Sharing from "expo-sharing";
import { useRouter } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { API_BASE_URL, api } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { AppButton, Card, ErrorBanner, Faint, Screen, Title, TopBar } from "../../src/components/ui";
import { unregisterPushToken } from "../../src/native/pushNotifications";
import { colors } from "../../src/theme";
import { useState } from "react";

export default function AccountScreen() {
  const { driver, logout } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

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
      setError(err instanceof Error ? err.message : "Failed to export");
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
        <Title>Perfil</Title>
      </TopBar>

      {error && <ErrorBanner message={error} />}

      <Card>
        <Text style={styles.name}>{driver?.name}</Text>
        <Faint>{driver?.email}</Faint>
        {driver && !driver.email_verified && (
          <Text style={styles.unverified}>Email ainda não verificado</Text>
        )}
      </Card>

      <Card>
        <View style={styles.planHeader}>
          <Text style={styles.cardTitle}>Plano</Text>
          <Text style={styles.planPill}>GRÁTIS</Text>
        </View>
        <Faint style={{ marginTop: 4 }}>
          A Rinko está gratuita, sem limites, enquanto validamos o produto — Work Report, CSV,
          Ledger, exportação em .docx e evidence continuam liberados pra todo mundo.
        </Faint>
      </Card>

      <Card>
        <Text style={styles.cardTitle}>Seus dados, sem lock-in</Text>
        <AppButton
          title="Exportar sessões (.csv)"
          variant="secondary"
          onPress={handleExportCsv}
          loading={exporting}
          style={{ marginTop: 12 }}
        />
      </Card>

      <AppButton title="Sair" variant="danger" onPress={handleLogout} />
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
