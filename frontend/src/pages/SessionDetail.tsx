import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { formatCents, formatDate } from "../api/format";
import { getCurrentLocation, stampImageWithLocation } from "../api/locationStamp";
import type {
  Evidence,
  EvidenceKind,
  Package,
  PackageBulkImportResult,
  ReturnReason,
  WorkSession,
} from "../api/types";
import { StatusPill } from "../components/StatusPill";

const RETURN_REASONS: { value: ReturnReason; label: string }[] = [
  { value: "refused", label: "Recusado" },
  { value: "wrong_address", label: "Endereço errado" },
  { value: "damaged", label: "Danificado" },
  { value: "undeliverable", label: "Não entregável" },
  { value: "other", label: "Outro" },
];

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

  const [packages, setPackages] = useState<Package[]>([]);
  const [importCourier, setImportCourier] = useState("uniuni");
  const [importText, setImportText] = useState("");
  const [importing, setImporting] = useState(false);
  const [refreshingStatus, setRefreshingStatus] = useState(false);
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [resolveOutcome, setResolveOutcome] = useState<"delivered" | "returned">("delivered");
  const [resolveReturnReason, setResolveReturnReason] = useState<ReturnReason>("wrong_address");

  function load() {
    if (!sessionId) return;
    api.get<WorkSession>(`/sessions/${sessionId}`).then(setSession).catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load"));
    api.get<Evidence[]>(`/sessions/${sessionId}/evidence`).then(setEvidence).catch(() => {});
    api.get<Package[]>(`/sessions/${sessionId}/packages`).then(setPackages).catch(() => {});
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

  async function handleBulkImport(e: FormEvent) {
    e.preventDefault();
    if (!sessionId) return;
    const codes = importText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    if (codes.length === 0) return;

    setError(null);
    setImporting(true);
    try {
      const result = await api.post<PackageBulkImportResult>(
        `/sessions/${sessionId}/packages/bulk-import`,
        { tracking_codes: codes, courier_code: importCourier || null }
      );
      setImportText("");
      if (result.skipped_duplicates.length > 0) {
        setError(`${result.skipped_duplicates.length} código(s) já existiam nessa sessão e foram ignorados.`);
      }
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to import packages");
    } finally {
      setImporting(false);
    }
  }

  async function handleRefreshStatus() {
    if (!sessionId) return;
    setError(null);
    setRefreshingStatus(true);
    try {
      await api.post(`/sessions/${sessionId}/packages/refresh-status`, {});
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to refresh carrier status");
    } finally {
      setRefreshingStatus(false);
    }
  }

  async function handleResolve(pkg: Package) {
    if (!sessionId) return;
    setError(null);
    try {
      await api.post(`/sessions/${sessionId}/packages/${pkg.id}/resolve`, {
        outcome: resolveOutcome,
        return_reason: resolveOutcome === "returned" ? resolveReturnReason : null,
      });
      setResolvingId(null);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to resolve package");
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
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ margin: 0 }}>Pacotes</h3>
            {packages.some((p) => p.source !== "manual") && (
              <button
                type="button"
                className="btn-ghost"
                onClick={handleRefreshStatus}
                disabled={refreshingStatus}
                style={{ fontSize: 13 }}
              >
                {refreshingStatus ? <span className="spinner" /> : "↻ Atualizar status"}
              </button>
            )}
          </div>

          <div style={{ marginTop: 12, marginBottom: 12 }}>
            {packages.length === 0 && <span className="faint">Nenhum pacote registrado ainda.</span>}
            {packages.map((pkg) => (
              <div
                key={pkg.id}
                className="row"
                style={{ flexDirection: "column", alignItems: "stretch", gap: 6, padding: "10px 0" }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span className="mono">{pkg.tracking_code}</span>
                  {pkg.outcome === null ? (
                    <span className="pill pill-pending">Pendente</span>
                  ) : (
                    <span className={`pill ${pkg.outcome === "delivered" ? "pill-good" : "pill-bad"}`}>
                      {pkg.outcome === "delivered" ? "Entregue" : "Devolvido"}
                    </span>
                  )}
                </div>
                {pkg.carrier_status && (
                  <span className="faint" style={{ fontSize: 12 }}>
                    {pkg.source !== "manual" ? pkg.source.toUpperCase() : ""} · {pkg.carrier_status}
                  </span>
                )}

                {pkg.outcome === null && resolvingId !== pkg.id && (
                  <button
                    type="button"
                    className="btn-ghost"
                    style={{ alignSelf: "flex-start", fontSize: 13 }}
                    onClick={() => setResolvingId(pkg.id)}
                  >
                    Confirmar entrega/devolução
                  </button>
                )}

                {resolvingId === pkg.id && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    <select
                      value={resolveOutcome}
                      onChange={(e) => setResolveOutcome(e.target.value as "delivered" | "returned")}
                    >
                      <option value="delivered">Entregue</option>
                      <option value="returned">Devolvido</option>
                    </select>
                    {resolveOutcome === "returned" && (
                      <select
                        value={resolveReturnReason}
                        onChange={(e) => setResolveReturnReason(e.target.value as ReturnReason)}
                      >
                        {RETURN_REASONS.map((r) => (
                          <option key={r.value} value={r.value}>
                            {r.label}
                          </option>
                        ))}
                      </select>
                    )}
                    <div style={{ display: "flex", gap: 8 }}>
                      <button type="button" className="btn btn-primary" onClick={() => handleResolve(pkg)}>
                        Confirmar
                      </button>
                      <button type="button" className="btn-ghost" onClick={() => setResolvingId(null)}>
                        Cancelar
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          <form onSubmit={handleBulkImport}>
            <div className="field">
              <label htmlFor="importCourier">Transportadora</label>
              <select
                id="importCourier"
                value={importCourier}
                onChange={(e) => setImportCourier(e.target.value)}
              >
                <option value="uniuni">UniUni</option>
                <option value="gofo">GOFO</option>
                <option value="">Detectar automaticamente</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="importCodes">Códigos de rastreio (um por linha)</label>
              <textarea
                id="importCodes"
                rows={4}
                value={importText}
                onChange={(e) => setImportText(e.target.value)}
                placeholder={"LV209031969CN\nLV209031970CN"}
              />
            </div>
            <button
              type="submit"
              className="btn btn-secondary"
              disabled={importing || !importText.trim()}
            >
              {importing ? <span className="spinner" /> : "Importar pacotes"}
            </button>
          </form>
        </div>

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
