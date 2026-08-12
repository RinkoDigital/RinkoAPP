import { Redirect, Tabs } from "expo-router";
import { Text } from "react-native";
import { useAuth } from "../../src/auth/AuthContext";
import { LoadingScreen } from "../../src/components/ui";
import { colors } from "../../src/theme";

export default function TabsLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <LoadingScreen />;
  if (!isAuthenticated) return <Redirect href="/auth" />;

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.crimsonGlow,
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
        options={{ title: "Home", tabBarIcon: () => <Text>🏠</Text> }}
      />
      <Tabs.Screen
        name="ledger"
        options={{ title: "Ledger", tabBarIcon: () => <Text>📒</Text> }}
      />
      <Tabs.Screen
        name="account"
        options={{ title: "Account", tabBarIcon: () => <Text>👤</Text> }}
      />
    </Tabs>
  );
}
