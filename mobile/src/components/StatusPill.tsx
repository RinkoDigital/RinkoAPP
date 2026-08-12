import { StyleSheet, Text } from "react-native";
import { colors, radii } from "../theme";
import type { PaymentStatus } from "../api/types";

const LABELS: Record<PaymentStatus, string> = {
  pending: "Pending",
  partial: "Partial",
  received: "Received",
};

const COLOR_MAP: Record<PaymentStatus, { bg: string; fg: string }> = {
  pending: { bg: colors.pendingBg, fg: colors.pending },
  partial: { bg: colors.badBg, fg: colors.bad },
  received: { bg: colors.goodBg, fg: colors.good },
};

export function StatusPill({ status }: { status: PaymentStatus }) {
  const { bg, fg } = COLOR_MAP[status];
  return (
    <Text style={[styles.pill, { backgroundColor: bg, color: fg }]}>{LABELS[status]}</Text>
  );
}

const styles = StyleSheet.create({
  pill: {
    paddingVertical: 3,
    paddingHorizontal: 10,
    borderRadius: radii.pill,
    fontSize: 11,
    fontWeight: "700",
    textTransform: "uppercase",
    overflow: "hidden",
  },
});
