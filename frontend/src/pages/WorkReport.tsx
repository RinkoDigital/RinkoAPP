import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "../api/client";
import { formatCents, formatDate, formatTime } from "../api/format";
import type { WorkReport } from "../api/types";

export function WorkReportPage() {
  const { t } = useTranslation();
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<WorkReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    api
      .get<WorkReport>(`/sessions/${sessionId}/work-report`)
      .then(setReport)
      .catch((err) => setError(err instanceof ApiError ? err.message : t("workReport.errors.loadFailed")));
  }, [sessionId, t]);

  async function handleDownloadDocx() {
    if (!sessionId) return;
    setDownloadError(null);
    setDownloading(true);
    try {
      const blob = await api.get<Blob>(`/sessions/${sessionId}/work-report.docx`);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `work_report_${report?.report_number ?? sessionId}.docx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      if (err instanceof ApiError && err.status === 402) {
        setDownloadError(t("workReport.errors.proFeature"));
      } else {
        setDownloadError(err instanceof ApiError ? err.message : t("workReport.errors.downloadFailed"));
      }
    } finally {
      setDownloading(false);
    }
  }

  if (error) {
    return (
      <div className="app-shell">
        <div className="screen">
          <div className="error-banner">{error}</div>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="app-shell">
        <div className="screen empty-state">
          <span className="spinner" />
        </div>
      </div>
    );
  }

  const diff = report.compensation.difference_cents;

  return (
    <div className="app-shell">
      <div className="top-bar">
        <button className="btn-ghost" onClick={() => navigate(-1)}>
          {t("workReport.back")}
        </button>
      </div>
      <div className="screen">
        <div className="card decorated">
          <div
            className="glow"
            aria-hidden="true"
            style={{ top: -70, left: "50%", transform: "translateX(-50%)", width: 220, height: 220 }}
          />
          <div
            className="wordmark"
            style={{ color: "var(--violet-glow)", fontSize: "0.9rem", position: "relative", zIndex: 1 }}
          >
            {t("workReport.title")}
          </div>
          <div className="faint" style={{ marginTop: 4, position: "relative", zIndex: 1 }}>
            {report.report_number}
          </div>

          <div className="row">
            <span className="label">{t("workReport.driver")}</span>
            <span>{report.driver_name}</span>
          </div>
          <div className="row">
            <span className="label">{t("workReport.carrier")}</span>
            <span>{report.carrier_name}</span>
          </div>
          <div className="row">
            <span className="label">{t("workReport.serviceDate")}</span>
            <span>{formatDate(report.service_date)}</span>
          </div>
          {report.route_id && (
            <div className="row">
              <span className="label">{t("workReport.routeId")}</span>
              <span className="mono">{report.route_id}</span>
            </div>
          )}
        </div>

        <div className="card">
          <h3 style={{ marginTop: 0 }}>{t("workReport.workRecord.title")}</h3>
          <div className="row">
            <span className="label">{t("workReport.workRecord.routeStarted")}</span>
            <span className="mono">{formatTime(report.work_record.route_started)}</span>
          </div>
          <div className="row">
            <span className="label">{t("workReport.workRecord.routeCompleted")}</span>
            <span className="mono">{formatTime(report.work_record.route_completed)}</span>
          </div>
          <div className="row">
            <span className="label">{t("workReport.workRecord.packagesAssigned")}</span>
            <span className="mono">{report.work_record.packages_assigned}</span>
          </div>
          <div className="row">
            <span className="label">{t("workReport.workRecord.completed")}</span>
            <span className="mono">{report.work_record.packages_completed}</span>
          </div>
          <div className="row">
            <span className="label">{t("workReport.workRecord.exceptions")}</span>
            <span className="mono">{report.work_record.exceptions}</span>
          </div>
          <div className="row">
            <span className="label">{t("workReport.workRecord.distance")}</span>
            <span className="mono">{report.work_record.mileage ?? "—"} mi</span>
          </div>
        </div>

        <div className="card">
          <h3 style={{ marginTop: 0 }}>{t("workReport.compensation.title")}</h3>
          <div className="row">
            <span className="label">{t("workReport.compensation.agreedRate")}</span>
            <span className="mono">{formatCents(report.compensation.agreed_rate_cents)}/pkg</span>
          </div>
          <div className="row">
            <span className="label">{t("workReport.compensation.expectedGross")}</span>
            <span className="mono">{formatCents(report.compensation.expected_gross_cents)}</span>
          </div>
          <div className="row">
            <span className="label">{t("workReport.compensation.paymentDue")}</span>
            <span>{formatDate(report.compensation.payment_due_date)}</span>
          </div>
          <div className="row">
            <span className="label">{t("workReport.compensation.paymentStatus")}</span>
            <span style={{ textTransform: "uppercase" }}>{report.compensation.payment_status}</span>
          </div>
          {report.compensation.payment_received_cents !== null && (
            <div className="row">
              <span className="label">{t("workReport.compensation.received")}</span>
              <span className="mono">{formatCents(report.compensation.payment_received_cents)}</span>
            </div>
          )}
          {diff !== null && diff !== undefined && (
            <div className="row">
              <span className="label">{t("workReport.compensation.difference")}</span>
              <span className="mono" style={{ color: diff < 0 ? "var(--bad)" : "var(--good)" }}>
                {formatCents(diff)}
              </span>
            </div>
          )}
        </div>

        <div className="card">
          <h3 style={{ marginTop: 0 }}>{t("workReport.supportingRecords.title")}</h3>
          {report.supporting_records.length === 0 && (
            <span className="faint">{t("workReport.supportingRecords.none")}</span>
          )}
          {report.supporting_records.map((ev) => (
            <div key={ev.id} className="row">
              <span>✓ {ev.kind.replace(/_/g, " ")}</span>
            </div>
          ))}
        </div>

        {diff !== null && diff !== undefined && diff !== 0 && (
          <p className="faint" style={{ fontStyle: "italic" }}>
            {t("workReport.disclaimer")}
          </p>
        )}

        {downloadError && <div className="error-banner">{downloadError}</div>}
        <button className="btn btn-secondary" onClick={handleDownloadDocx} disabled={downloading}>
          {downloading ? <span className="spinner" /> : t("workReport.downloadDocx")}
        </button>
      </div>
    </div>
  );
}
