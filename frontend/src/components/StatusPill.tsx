import type { PaymentStatus } from "../api/types";

const LABELS: Record<PaymentStatus, string> = {
  pending: "Pending",
  partial: "Partial",
  received: "Received",
};

const CLASSES: Record<PaymentStatus, string> = {
  pending: "pill pill-pending",
  partial: "pill pill-bad",
  received: "pill pill-good",
};

export function StatusPill({ status }: { status: PaymentStatus }) {
  return <span className={CLASSES[status]}>{LABELS[status]}</span>;
}
