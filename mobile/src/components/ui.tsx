import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
  type ViewProps,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { colors, radii } from "../theme";

export function Screen({
  children,
  scroll = true,
  style,
}: {
  children: React.ReactNode;
  scroll?: boolean;
  style?: ViewProps["style"];
}) {
  const inner = (
    <View style={[styles.screenInner, style]}>{children}</View>
  );
  return (
    <SafeAreaView style={styles.screen} edges={["top", "bottom"]}>
      {scroll ? (
        <ScrollView contentContainerStyle={styles.scrollContent}>{inner}</ScrollView>
      ) : (
        inner
      )}
    </SafeAreaView>
  );
}

export function TopBar({ children }: { children: React.ReactNode }) {
  return <View style={styles.topBar}>{children}</View>;
}

export function Title({ children }: { children: React.ReactNode }) {
  return <Text style={styles.title}>{children}</Text>;
}

export function Wordmark({ children, size = 32 }: { children: React.ReactNode; size?: number }) {
  return <Text style={[styles.wordmark, { fontSize: size }]}>{children}</Text>;
}

export function Card({ children, style }: { children: React.ReactNode; style?: ViewProps["style"] }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function Muted({ children, style }: { children: React.ReactNode; style?: any }) {
  return <Text style={[styles.muted, style]}>{children}</Text>;
}

export function Faint({ children, style }: { children: React.ReactNode; style?: any }) {
  return <Text style={[styles.faint, style]}>{children}</Text>;
}

export function Mono({ children, style }: { children: React.ReactNode; style?: any }) {
  return <Text style={[styles.mono, style]}>{children}</Text>;
}

export function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      {typeof value === "string" || typeof value === "number" ? (
        <Text style={styles.rowValue}>{value}</Text>
      ) : (
        value
      )}
    </View>
  );
}

export function Field({
  label,
  ...inputProps
}: { label: string } & TextInputProps) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        placeholderTextColor={colors.textFaint}
        style={styles.input}
        {...inputProps}
      />
    </View>
  );
}

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

export function AppButton({
  title,
  onPress,
  variant = "primary",
  loading = false,
  disabled = false,
  style,
}: {
  title: string;
  onPress: () => void;
  variant?: ButtonVariant;
  loading?: boolean;
  disabled?: boolean;
  style?: ViewProps["style"];
}) {
  const isDisabled = disabled || loading;
  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      style={[
        styles.btn,
        variant === "primary" && styles.btnPrimary,
        variant === "secondary" && styles.btnSecondary,
        variant === "ghost" && styles.btnGhost,
        variant === "danger" && styles.btnDanger,
        isDisabled && styles.btnDisabled,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={variant === "primary" ? colors.accentInk : colors.violetGlow} />
      ) : (
        <Text
          style={[
            styles.btnText,
            variant === "primary" && styles.btnTextPrimary,
            variant === "ghost" && styles.btnTextGhost,
            variant === "danger" && styles.btnTextDanger,
          ]}
        >
          {title}
        </Text>
      )}
    </Pressable>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <View style={styles.errorBanner}>
      <Text style={styles.errorText}>{message}</Text>
    </View>
  );
}

export function EmptyState({ children }: { children: React.ReactNode }) {
  return (
    <View style={styles.emptyState}>
      <Text style={styles.emptyStateText}>{children}</Text>
    </View>
  );
}

export function LoadingScreen() {
  return (
    <SafeAreaView style={[styles.screen, styles.centerAll]}>
      <ActivityIndicator color={colors.violetGlow} size="large" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  centerAll: {
    alignItems: "center",
    justifyContent: "center",
  },
  scrollContent: {
    flexGrow: 1,
  },
  screenInner: {
    padding: 20,
    paddingBottom: 96,
  },
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 6,
  },
  title: {
    fontFamily: "serif",
    fontSize: 18,
    color: colors.text,
    fontWeight: "600",
  },
  wordmark: {
    fontFamily: "serif",
    letterSpacing: 4,
    color: colors.violetGlow,
    textAlign: "center",
  },
  card: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radii.card,
    padding: 18,
    marginBottom: 14,
  },
  muted: {
    color: colors.textMuted,
  },
  faint: {
    color: colors.textFaint,
    fontSize: 13,
  },
  mono: {
    fontFamily: "monospace",
    color: colors.text,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "baseline",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
  },
  rowLabel: {
    color: colors.textMuted,
    fontSize: 14,
  },
  rowValue: {
    color: colors.text,
    fontSize: 14,
  },
  field: {
    marginBottom: 14,
  },
  fieldLabel: {
    color: colors.textMuted,
    fontSize: 13,
    marginBottom: 6,
  },
  input: {
    backgroundColor: colors.cardSunken,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radii.input,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    color: colors.text,
  },
  btn: {
    borderRadius: radii.input,
    paddingVertical: 13,
    paddingHorizontal: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  btnPrimary: {
    backgroundColor: colors.violet,
  },
  btnSecondary: {
    backgroundColor: "transparent",
    borderWidth: 1,
    borderColor: colors.line,
  },
  btnGhost: {
    backgroundColor: "transparent",
    paddingVertical: 6,
    paddingHorizontal: 0,
  },
  btnDanger: {
    backgroundColor: "transparent",
    borderWidth: 1,
    borderColor: colors.bad,
  },
  btnDisabled: {
    opacity: 0.5,
  },
  btnText: {
    fontSize: 15,
    fontWeight: "600",
    color: colors.text,
  },
  btnTextPrimary: {
    color: colors.accentInk,
  },
  btnTextGhost: {
    color: colors.violetGlow,
  },
  btnTextDanger: {
    color: colors.bad,
  },
  errorBanner: {
    backgroundColor: colors.badBg,
    borderWidth: 1,
    borderColor: colors.bad,
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
  },
  errorText: {
    color: colors.bad,
    fontSize: 13,
  },
  emptyState: {
    alignItems: "center",
    padding: 40,
  },
  emptyStateText: {
    color: colors.textFaint,
    textAlign: "center",
  },
});
