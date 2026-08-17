import AsyncStorage from "@react-native-async-storage/async-storage";

export type QuickReportStatus = "COMPLETE" | "PARTIAL" | "ATTENTION";

export type QuickReport = {
  id: string;
  company: string;
  driver: string;
  date: string;
  total: number;
  delivered: number;
  notDelivered: number;
  rate: number;
  status: QuickReportStatus;
  route: string;
  notes: string;
};

const STORAGE_KEY = "shiftproof_quick_reports";
const COUNTER_PREFIX = "shiftproof_quick_report_counter_";

export function formatQuickReportDate(date: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(date);
}

function dateKey(date: Date = new Date()): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}${m}${d}`;
}

export function quickReportStatus(rate: number): QuickReportStatus {
  if (rate === 100) return "COMPLETE";
  if (rate >= 90) return "PARTIAL";
  return "ATTENTION";
}

export async function nextQuickReportId(): Promise<string> {
  const key = `${COUNTER_PREFIX}${dateKey()}`;
  const stored = await AsyncStorage.getItem(key);
  const next = Number(stored ?? 0) + 1;
  await AsyncStorage.setItem(key, String(next));
  return `SP-${dateKey()}-${String(next).padStart(3, "0")}`;
}

export async function getQuickReports(): Promise<QuickReport[]> {
  const raw = await AsyncStorage.getItem(STORAGE_KEY);
  return raw ? JSON.parse(raw) : [];
}

export async function getQuickReport(id: string): Promise<QuickReport | null> {
  const reports = await getQuickReports();
  return reports.find((r) => r.id === id) ?? null;
}

export async function saveQuickReport(report: QuickReport): Promise<QuickReport[]> {
  const reports = await getQuickReports();
  const updated = [report, ...reports.filter((r) => r.id !== report.id)];
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return updated;
}

export async function deleteQuickReport(id: string): Promise<QuickReport[]> {
  const reports = await getQuickReports();
  const updated = reports.filter((r) => r.id !== id);
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return updated;
}
