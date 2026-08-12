import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { formatCents, formatDate } from "../api/format";
import { getCurrentLocation, stampImageWithLocation } from "../api/locationStamp";
import type { Evidence, EvidenceKind, WorkSession } from "../api/types";
import { StatusPill } from "../components/StatusPill";

const EVIDENCE_KINDS: { value: EvidenceKind; label: string }[] = [
  { value: "route_screenshot", label: "Route screenshot" },
  { value: "rate_screenshot", label: "Rate screenshot" },
  { value: "gps_session", label: "GPS session" },
  { value: "completion_record", label: "Completion record" },
  { value: "settlement_statement", label: "Settlement statement" },
  { value: "other", label: "Other" },
];

export function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<WorkSession | null>(null);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [exceptionsCount, setExceptionsCount] = useState("0");
  const [mileage, setMileage] = useState("");
  const [closing, setClosing] = useState(false);

  const [paymentReceived, setPaymentReceived] = useState("");
  const [recordingPayment, setRecordingPayment] = useState(false);

  const [evidenceKind, setEvidenceKind] = useState<EvidenceKind>("route_screenshot");
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null);
  const [uploadingEvidence, setUploadingEvidence] = useState(false);

  function load() {
    if (!sessionId) return;
    api.get<WorkSession>(`/sessions/${sessionId}`).then(setSession).catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load"));
    api.get<Evidence[]>(`/sessions/${sessionId}/evidence`).then(setEvidence).catch(() => {});
  }

  useEffect(load, [sessionId]);

  async function handleClose(e: FormEvent) {
    e.preventDefault();
    if (!sessionId) return;
    setError(null);
    setClosing(true);
    try {
      await api.post<WorkSession>(`/sessions/${sessionId}/close`, {
        exceptions_count: parseInt(exceptionsCount || "0", 10),
        mileage: mileage ? parseFloat(mileage) : null,
      });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to close session");
    } finally {
      setClosing(false);
    }
  }

  async function handleRecordPayment(e: FormEvent) {
    e.preventDefault();
    if (!sessionId || !paymentReceived) return;
    setError(null);
    setRecordingPayment(true);
    try {
      await api.post<WorkSession>(`/sessions/${sessionId}/record-payment`, {
        payment_received_cents: Math.round(parseFloat(paymentReceived) * 100),
      });
      setPaymentReceived("");
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to record payment");
    } finally {
      setRecordingPayment(false);
    }
  }

  async function handleUploadEvidence(e: FormEvent) {
    e.preventDefault();
    if (!sessionId || !evidenceFile) return;
    setError(null);
    setUploadingEvidence(true);
    try {
      let fileToUpload = evidenceFile;
      const coords = evidenceFile.type.startsWith("image/") ? await getCurrentLocation() : null;
      if (coords) {
        fileToUpload = await stampImageWithLocation(evidenceFile, coords);
      }

      const form = new FormData();
      form.append("kind", evidenceKind);
      form.append("file", fileToUpload);
      if (coords) {
        form.append("latitude", String(coords.latitude));
        form.append("longitude", String(coords.longitude));
        if (coords.address) {
          form.append("address", coords.address);
        }
        form.append("captured_at", coords.capturedAt);
      }
      await api.postForm<Evidence>(`/sessions/${sessionId}/evidence`, form);
      setEvidenceFile(null);
      load();
    } catch (err) {
      if (err instanceof ApiError && err.status === 402) {
        setError(`${err.message}`);
      } else {
        setError(err instanceof ApiError ? err.message : "Failed to upload evidence");
      }
    } finally {
      setUploadingEvidence(false);
    }
  }

  if (error && !session) {
    return (
      <div className="app-shell">
        <div className="screen">
          <div className="error-banner">{error}</div>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="app-shell">
        <div className="screen empty-state">
          <span className="spinner" />
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <div className="top-bar">
        <button className="btn-ghost" onClick={() => navigate(-1)}>
          ← Voltar
        </button>
      </div>
      <div className="screen">
        {error && <div className="error-banner">{error}</div>}

        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <div>
              <strong>{session.carrier_name}</strong>
              {session.route_id && <span className="faint"> · {session.route_id}</span>}
            </div>
            <StatusPill status={session.status === "open" ? "pending" : session.payment_status} />
          </div>
          <div className="faint">{formatDate(session.service_date)}</div>

          <div className="row">
            <span className="label">Packages assigned</span>
            <span className="mono">{session.packages_assigned}</span>
          </div>
          <div className="row">
            <span className="label">Packages completed</span>
            <span className="mono">{session.packages_completed}</span>
          </div>
          <div className="row">
            <span className="label">Agreed rate</span>
            <span className="mono">{formatCents(session.agreed_rate_cents)}/pkg</span>
          </div>
          {session.expected_gross_cents !== null && (
            <div className="row">
              <span className="label">Expected gross</span>
              <span className="mono">{formatCents(session.expected_gross_cents)}</span>
            </div>
          )}
          {session.status === "closed" && (
            <div className="row">
              <span className="label">Outstanding</span>
              <span className="mono">{formatCents(session.outstanding_cents)}</span>
            </div>
          )}
        </div>

        {session.status === "open" && (
          <form onSubmit={handleClose} className="card">
            <h3 style={{ marginTop: 0 }}>Encerrar sessão</h3>
            <div className="field">
              <label htmlFor="exceptions">Exceptions</label>
              <input
                id="exceptions"
                type="number"
                min={0}
                value={exceptionsCount}
                onChange={(e) => setExceptionsCount(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="mileage">Mileage</label>
              <input
                id="mileage"
                type="number"
                step="0.1"
                min={0}
                value={mileage}
                onChange={(e) => setMileage(e.target.value)}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={closing}>
              {closing ? <span className="spinner" /> : "Encerrar e gerar Work Report"}
            </button>
          </form>
        )}

        {session.status === "closed" && session.payment_status !== "received" && (
          <form onSubmit={handleRecordPayment} className="card">
            <h3 style={{ marginTop: 0 }}>Registrar pagamento recebido</h3>
            <div className="field">
              <label htmlFor="received">Recebido ($)</label>
              <input
                id="received"
                type="number"
                step="0.01"
                min={0}
                value={paymentReceived}
                onChange={(e) => setPaymentReceived(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={recordingPayment}>
              {recordingPayment ? <span className="spinner" /> : "Registrar pagamento"}
            </button>
          </form>
        )}

        <div className="card">
          <h3 style={{ marginTop: 0 }}>Evidence</h3>
          <div style={{ marginBottom: 12 }}>
            {evidence.length === 0 && <span className="faint">Nenhuma evidência anexada ainda.</span>}
            {evidence.map((ev) => (
              <a
                key={ev.id}
                href={api.downloadUrl(ev.file_url)}
                target="_blank"
                rel="noreferrer"
                className="evidence-chip"
                style={{ color: "inherit", textDecoration: "none" }}
              >
                ✓ {EVIDENCE_KINDS.find((k) => k.value === ev.kind)?.label ?? ev.kind}
                {ev.latitude !== null && " 📍"}
              </a>
            ))}
          </div>

          <form onSubmit={handleUploadEvidence}>
            <div className="field">
              <label htmlFor="evidenceKind">Tipo</label>
              <select
                id="evidenceKind"
                value={evidenceKind}
                onChange={(e) => setEvidenceKind(e.target.value as EvidenceKind)}
              >
                {EVIDENCE_KINDS.map((k) => (
                  <option key={k.value} value={k.value}>
                    {k.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="evidenceFile">Arquivo</label>
              <input
                id="evidenceFile"
                type="file"
                accept="image/png,image/jpeg,image/webp,application/pdf"
                onChange={(e) => setEvidenceFile(e.target.files?.[0] ?? null)}
              />
            </div>
            <button type="submit" className="btn btn-secondary" disabled={uploadingEvidence || !evidenceFile}>
              {uploadingEvidence ? <span className="spinner" /> : "Anexar evidência"}
            </button>
          </form>
        </div>

        {session.status === "closed" && (
          <Link to={`/sessions/${session.id}/report`} className="btn btn-primary" style={{ marginTop: 14, textDecoration: "none" }}>
            Ver Work Report
          </Link>
        )}
      </div>
    </div>
  );
}
