import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { formatCents, formatDate } from "../api/format";
import type { LedgerSummary, WorkSession } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { BottomNav } from "../components/BottomNav";
import { StatusPill } from "../components/StatusPill";

export function HomePage() {
  const { driver } = useAuth();
  const [ledger, setLedger] = useState<LedgerSummary | null>(null);
  const [sessions, setSessions] = useState<WorkSession[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.get<LedgerSummary>("/ledger"), api.get<WorkSession[]>("/sessions")])
      .then(([ledgerData, sessionsData]) => {
        setLedger(ledgerData);
        setSessions(sessionsData);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load"));
  }, []);

  const firstName = driver?.name.split(" ")[0] ?? "";

  return (
    <div className="app-shell">
      <div className="top-bar">
        <h1>Boa tarde, {firstName}</h1>
      </div>
      <div className="screen">
        {error && <div className="error-banner">{error}</div>}

        <div className="card" style={{ background: "var(--surface-2)" }}>
          <div className="faint">OUTSTANDING EARNINGS</div>
          <div className="mono" style={{ fontSize: "2rem", color: "var(--crimson-glow)", marginTop: 4 }}>
            {ledger ? formatCents(ledger.outstanding_total_cents) : <span className="spinner" />}
          </div>
          <Link to="/ledger" className="btn-ghost">
            Ver payment ledger →
          </Link>
        </div>

        <h3 style={{ marginTop: 24, marginBottom: 8 }}>Sessões recentes</h3>
        {sessions === null && <div className="empty-state">Carregando…</div>}
        {sessions !== null && sessions.length === 0 && (
          <div className="empty-state">Nenhuma work session ainda. Toque em + para começar.</div>
        )}
        {sessions?.map((s) => (
          <Link key={s.id} to={`/sessions/${s.id}`} style={{ textDecoration: "none", color: "inherit" }}>
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <div>
                  <strong>{s.carrier_name}</strong>
                  {s.route_id && <span className="faint"> · {s.route_id}</span>}
                </div>
                <StatusPill status={s.status === "open" ? "pending" : s.payment_status} />
              </div>
              <div className="faint" style={{ marginTop: 4 }}>
                {formatDate(s.service_date)} · {s.packages_completed}/{s.packages_assigned} pacotes
              </div>
              <div className="mono" style={{ marginTop: 6 }}>
                {formatCents(s.expected_gross_cents)}
              </div>
            </div>
          </Link>
        ))}
      </div>

      <Link to="/sessions/new" className="fab" aria-label="Iniciar work session">
        +
      </Link>
      <BottomNav />
    </div>
  );
}
