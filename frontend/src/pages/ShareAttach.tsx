import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Evidence, EvidenceKind, WorkSession } from "../api/types";
import type { SharedItem } from "../native/shareTarget";
import { sharedItemToFile } from "../native/shareTarget";

const EVIDENCE_KINDS: { value: EvidenceKind; label: string }[] = [
  { value: "route_screenshot", label: "Route screenshot" },
  { value: "rate_screenshot", label: "Rate screenshot" },
  { value: "gps_session", label: "GPS session" },
  { value: "completion_record", label: "Completion record" },
  { value: "settlement_statement", label: "Settlement statement" },
  { value: "other", label: "Other" },
];

export function ShareAttachPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [openSessions, setOpenSessions] = useState<WorkSession[] | null>(null);
  const [sessionId, setSessionId] = useState("");
  const [kind, setKind] = useState<EvidenceKind>("other");
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    const item = (location.state as { item?: SharedItem } | null)?.item;
    if (!item) {
      setError("Nenhum arquivo compartilhado foi encontrado.");
      return;
    }
    const f = sharedItemToFile(item);
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
  }, [location.state]);

  useEffect(() => {
    api
      .get<WorkSession[]>("/sessions?status=open")
      .then((sessions) => {
        setOpenSessions(sessions);
        if (sessions.length > 0) setSessionId(sessions[0].id);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load sessions"));
  }, []);

  const isImage = useMemo(() => file?.type.startsWith("image/") ?? false, [file]);

  async function handleAttach() {
    if (!file || !sessionId) return;
    setError(null);
    setUploading(true);
    try {
      const form = new FormData();
      form.append("kind", kind);
      form.append("file", file);
      await api.postForm<Evidence>(`/sessions/${sessionId}/evidence`, form);
      navigate(`/sessions/${sessionId}`, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to attach evidence");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="top-bar">
        <h1>Anexar à Rinko</h1>
      </div>
      <div className="screen">
        {error && <div className="error-banner">{error}</div>}

        {file && (
          <div className="card">
            {isImage && previewUrl ? (
              <img src={previewUrl} alt="Pré-visualização" style={{ width: "100%", borderRadius: 10 }} />
            ) : (
              <div className="faint">{file.name}</div>
            )}
          </div>
        )}

        {openSessions !== null && openSessions.length === 0 && (
          <div className="empty-state">
            Nenhuma work session aberta pra anexar isso. Inicie uma sessão e compartilhe de novo.
          </div>
        )}

        {openSessions !== null && openSessions.length > 0 && (
          <div className="card">
            <div className="field">
              <label htmlFor="session">Work session</label>
              <select id="session" value={sessionId} onChange={(e) => setSessionId(e.target.value)}>
                {openSessions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.carrier_name}
                    {s.route_id ? ` · ${s.route_id}` : ""}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="kind">Tipo de evidência</label>
              <select id="kind" value={kind} onChange={(e) => setKind(e.target.value as EvidenceKind)}>
                {EVIDENCE_KINDS.map((k) => (
                  <option key={k.value} value={k.value}>
                    {k.label}
                  </option>
                ))}
              </select>
            </div>

            <button className="btn btn-primary" onClick={handleAttach} disabled={!file || uploading}>
              {uploading ? <span className="spinner" /> : "Anexar evidência"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
