import { useEffect } from "react";
import { Redirect, Tabs } from "expo-router";
import { Text } from "react-native";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../src/auth/AuthContext";
import { LoadingScreen } from "../../src/components/ui";
import { syncPushTokenWithBackend } from "../../src/native/pushNotifications";
import { colors } from "../../src/theme";

export default function TabsLayout() {
  const { t } = useTranslation();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) return;
    syncPushTokenWithBackend();
  }, [isAuthenticated]);

  if (isLoading) return <LoadingScreen />;
  if (!isAuthenticated) return <Redirect href="/auth" />;

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.violetGlow,
        tabBarInactiveTintColor: colors.textFaint,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.line,
        },
        tabBarLabelStyle: { fontSize: 11, letterSpacing: 0.3 },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{ title: t("nav.home"), tabBarIcon: () => <Text>🏠</Text> }}
      />
      <Tabs.Screen
        name="ledger"
        options={{ title: t("nav.ledger"), tabBarIcon: () => <Text>📒</Text> }}
      />
      <Tabs.Screen
        name="account"
        options={{ title: t("nav.account"), tabBarIcon: () => <Text>👤</Text> }}
      />
    </Tabs>
  );
}
