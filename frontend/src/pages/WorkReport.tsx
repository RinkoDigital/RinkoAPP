import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { formatCents, formatDate, formatTime } from "../api/format";
import type { WorkReport } from "../api/types";

export function WorkReportPage() {
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
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load report"));
  }, [sessionId]);

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
        setDownloadError("Exportação .docx é um recurso Rinko Pro. O JSON do relatório continua grátis.");
      } else {
        setDownloadError(err instanceof ApiError ? err.message : "Failed to download");
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
          ← Voltar
        </button>
      </div>
      <div className="screen">
        <div className="card">
          <div className="wordmark" style={{ color: "var(--crimson-glow)", fontSize: "0.9rem" }}>
            RINKO — INDEPENDENT WORK RECORD
          </div>
          <div className="faint" style={{ marginTop: 4 }}>{report.report_number}</div>

          <div className="row">
            <span className="label">Driver</span>
            <span>{report.driver_name}</span>
          </div>
          <div className="row">
            <span className="label">Carrier / Contractor</span>
            <span>{report.carrier_name}</span>
          </div>
          <div className="row">
            <span className="label">Service date</span>
            <span>{formatDate(report.service_date)}</span>
          </div>
          {report.route_id && (
            <div className="row">
              <span className="label">Route ID</span>
              <span className="mono">{report.route_id}</span>
            </div>
          )}
        </div>

        <div className="card">
          <h3 style={{ marginTop: 0 }}>Work Record</h3>
          <div className="row">
            <span className="label">Route started</span>
            <span className="mono">{formatTime(report.work_record.route_started)}</span>
          </div>
          <div className="row">
            <span className="label">Route completed</span>
            <span className="mono">{formatTime(report.work_record.route_completed)}</span>
          </div>
          <div className="row">
            <span className="label">Packages assigned</span>
            <span className="mono">{report.work_record.packages_assigned}</span>
          </div>
          <div className="row">
            <span className="label">Completed</span>
            <span className="mono">{report.work_record.packages_completed}</span>
          </div>
          <div className="row">
            <span className="label">Exceptions</span>
            <span className="mono">{report.work_record.exceptions}</span>
          </div>
          <div className="row">
            <span className="label">Distance</span>
            <span className="mono">{report.work_record.mileage ?? "—"} mi</span>
          </div>
        </div>

        <div className="card">
          <h3 style={{ marginTop: 0 }}>Compensation Record</h3>
          <div className="row">
            <span className="label">Agreed rate</span>
            <span className="mono">{formatCents(report.compensation.agreed_rate_cents)}/pkg</span>
          </div>
          <div className="row">
            <span className="label">Expected gross</span>
            <span className="mono">{formatCents(report.compensation.expected_gross_cents)}</span>
          </div>
          <div className="row">
            <span className="label">Payment due</span>
            <span>{formatDate(report.compensation.payment_due_date)}</span>
          </div>
          <div className="row">
            <span className="label">Payment status</span>
            <span style={{ textTransform: "uppercase" }}>{report.compensation.payment_status}</span>
          </div>
          {report.compensation.payment_received_cents !== null && (
            <div className="row">
              <span className="label">Received</span>
              <span className="mono">{formatCents(report.compensation.payment_received_cents)}</span>
            </div>
          )}
          {diff !== null && diff !== undefined && (
            <div className="row">
              <span className="label">DIFFERENCE</span>
              <span className="mono" style={{ color: diff < 0 ? "var(--bad)" : "var(--good)" }}>
                {formatCents(diff)}
              </span>
            </div>
          )}
        </div>

        <div className="card">
          <h3 style={{ marginTop: 0 }}>Supporting Records</h3>
          {report.supporting_records.length === 0 && <span className="faint">Nenhuma evidência anexada.</span>}
          {report.supporting_records.map((ev) => (
            <div key={ev.id} className="row">
              <span>✓ {ev.kind.replace(/_/g, " ")}</span>
            </div>
          ))}
        </div>

        {diff !== null && diff !== undefined && diff !== 0 && (
          <p className="faint" style={{ fontStyle: "italic" }}>
            Isso não transforma automaticamente este relatório em prova conclusiva numa disputa
            legal — autenticidade, contrato e regras probatórias ainda importam — mas cria
            documentação contemporânea muito melhor do que reconstruir uma rota meses depois.
          </p>
        )}

        {downloadError && <div className="error-banner">{downloadError}</div>}
        <button className="btn btn-secondary" onClick={handleDownloadDocx} disabled={downloading}>
          {downloading ? <span className="spinner" /> : "Baixar .docx"}
        </button>
      </div>
    </div>
  );
}
