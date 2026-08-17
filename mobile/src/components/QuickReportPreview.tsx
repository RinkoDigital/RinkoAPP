import { StyleSheet, Text, View } from "react-native";
import type { QuickReport } from "../quickReports";

const PAPER = {
  bg: "#f5f5f7",
  ink: "#202126",
  muted: "#7d7e87",
  faint: "#858690",
  line: "#dddde2",
  purple: "#7c3aed",
  purple2: "#a78bfa",
};

const STATUS_STYLE = {
  COMPLETE: { bg: "#e5f7ee", fg: "#19734c" },
  PARTIAL: { bg: "#fff2df", fg: "#a46016" },
  ATTENTION: { bg: "#ffe7e7", fg: "#a43838" },
} as const;

function narrative(r: QuickReport): string {
  return `On ${r.date}, driver ${r.driver} completed a delivery route for ${r.company}. A total of ${r.total.toLocaleString()} boxes were scheduled for delivery, of which ${r.delivered.toLocaleString()} were successfully delivered and ${r.notDelivered.toLocaleString()} were not delivered. The recorded delivery completion rate was ${r.rate.toFixed(1)}%.`;
}

export function QuickReportPreview({ report }: { report: QuickReport }) {
  const status = STATUS_STYLE[report.status];
  return (
    <View style={styles.preview}>
      <View style={styles.top}>
        <View style={styles.topRow}>
          <View>
            <Text style={styles.brand}>SHIFT PROOF</Text>
            <Text style={styles.brandLabel}>DELIVERY OPERATIONS</Text>
          </View>
          <View style={[styles.status, { backgroundColor: status.bg }]}>
            <Text style={[styles.statusText, { color: status.fg }]}>{report.status}</Text>
          </View>
        </View>
        <Text style={styles.title}>Delivery Report</Text>
        <Text style={styles.date}>{report.date}</Text>
        <Text style={styles.reportId}>REPORT ID: {report.id}</Text>
      </View>

      <View style={styles.body}>
        <View style={styles.metaRow}>
          <Meta label="Company" value={report.company} />
          <Meta label="Driver" value={report.driver} />
        </View>

        <View style={styles.stats}>
          <Stat label="Total Boxes" value={report.total.toLocaleString()} />
          <Stat label="Delivered" value={report.delivered.toLocaleString()} color={PAPER.purple} />
          <Stat label="Not Delivered" value={report.notDelivered.toLocaleString()} color="#c74a4a" />
        </View>

        <View style={styles.rateRow}>
          <Text style={styles.rateLabel}>Delivery completion rate</Text>
          <Text style={styles.rateValue}>{report.rate.toFixed(1)}%</Text>
        </View>
        <View style={styles.barBg}>
          <View style={[styles.bar, { width: `${Math.min(report.rate, 100)}%` }]} />
        </View>

        <View style={styles.details}>
          <Detail label="Route / Shift" value={report.route} />
          <Detail label="Observations" value={report.notes} />
        </View>

        <Text style={styles.narrative}>{narrative(report)}</Text>

        <View style={styles.footer}>
          <Text style={styles.footerText}>SHIFT PROOF · DELIVERY RECORD</Text>
          <Text style={styles.footerText}>{report.date}</Text>
        </View>
      </View>
    </View>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.meta}>
      <Text style={styles.metaLabel}>{label}</Text>
      <Text style={styles.metaValue}>{value}</Text>
    </View>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <View style={styles.stat}>
      <Text style={[styles.statNumber, color ? { color } : null]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.detail}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={styles.detailValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  preview: { borderRadius: 17, overflow: "hidden", backgroundColor: PAPER.bg },
  top: { backgroundColor: "#1b1820", padding: 24, borderBottomWidth: 5, borderBottomColor: PAPER.purple },
  topRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" },
  brand: { fontSize: 11, fontWeight: "900", letterSpacing: 3, color: "#fff" },
  brandLabel: { fontSize: 8, color: "#b9bac1", letterSpacing: 1.5, marginTop: 3 },
  status: { paddingHorizontal: 9, paddingVertical: 6, borderRadius: 20 },
  statusText: { fontSize: 8, fontWeight: "900", letterSpacing: 1 },
  title: { fontSize: 27, fontWeight: "800", color: "#fff", marginTop: 22 },
  date: { fontSize: 11, color: "#c5c5cb", marginTop: 3 },
  reportId: { fontSize: 9, color: "#999aa4", marginTop: 5, letterSpacing: 0.7 },
  body: { padding: 23 },
  metaRow: { flexDirection: "row", gap: 13 },
  meta: { flex: 1, borderBottomWidth: 1, borderBottomColor: PAPER.line, paddingBottom: 9 },
  metaLabel: { fontSize: 8, color: PAPER.faint, textTransform: "uppercase", letterSpacing: 1 },
  metaValue: { fontSize: 14, fontWeight: "700", color: PAPER.ink, marginTop: 4 },
  stats: { flexDirection: "row", gap: 8, marginVertical: 20 },
  stat: { flex: 1, backgroundColor: "#fff", borderWidth: 1, borderColor: "#e2e2e7", borderRadius: 10, padding: 12 },
  statNumber: { fontSize: 22, fontWeight: "800", color: "#33343a" },
  statLabel: { fontSize: 7.5, color: PAPER.muted, textTransform: "uppercase", letterSpacing: 0.7, marginTop: 3 },
  rateRow: { flexDirection: "row", justifyContent: "space-between" },
  rateLabel: { fontSize: 10, color: "#6f7078" },
  rateValue: { fontSize: 10, fontWeight: "800", color: "#33343a" },
  barBg: { height: 8, backgroundColor: PAPER.line, borderRadius: 8, overflow: "hidden", marginTop: 7 },
  bar: { height: 8, backgroundColor: PAPER.purple2 },
  details: { marginTop: 22, paddingVertical: 15, borderTopWidth: 1, borderBottomWidth: 1, borderColor: PAPER.line },
  detail: { flexDirection: "row", marginVertical: 5 },
  detailLabel: { width: 105, fontSize: 8, color: PAPER.faint, textTransform: "uppercase", letterSpacing: 0.7 },
  detailValue: { flex: 1, fontSize: 10.5, color: "#44454d", lineHeight: 15 },
  narrative: { fontSize: 11.5, color: "#4b4c54", lineHeight: 18, marginTop: 20 },
  footer: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 24,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: PAPER.line,
  },
  footerText: { fontSize: 7.5, color: "#9697a0", letterSpacing: 0.5 },
});
