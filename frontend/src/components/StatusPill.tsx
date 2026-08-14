import { useTranslation } from "react-i18next";
import type { PaymentStatus } from "../api/types";

const CLASSES: Record<PaymentStatus, string> = {
  pending: "pill pill-pending",
  partial: "pill pill-bad",
  received: "pill pill-good",
};

export function StatusPill({ status }: { status: PaymentStatus }) {
  const { t } = useTranslation();
  return <span className={CLASSES[status]}>{t(`statusPill.${status}`)}</span>;
}
