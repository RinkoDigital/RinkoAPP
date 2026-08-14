import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "../api/client";
import { formatCents, formatDate } from "../api/format";
import type { LedgerSummary, WorkSession } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { BottomNav } from "../components/BottomNav";
import { StatusPill } from "../components/StatusPill";

export function HomePage() {
  const { t } = useTranslation();
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
      .catch((err) => setError(err instanceof ApiError ? err.message : t("common.failedToLoad")));
  }, [t]);

  const firstName = driver?.name.split(" ")[0] ?? "";

  return (
    <div className="app-shell">
      <div className="top-bar decorated">
        <div
          className="glow"
          aria-hidden="true"
          style={{ top: -90, right: -40, width: 180, height: 180 }}
        />
        <h1 style={{ position: "relative", zIndex: 1 }}>{t("home.greeting", { name: firstName })}</h1>
      </div>
      <div className="screen">
        {error && <div className="error-banner">{error}</div>}

        <div className="card" style={{ background: "var(--surface-2)" }}>
          <div className="faint">{t("home.outstandingEarnings")}</div>
          <div className="mono" style={{ fontSize: "2rem", color: "var(--violet-glow)", marginTop: 4 }}>
            {ledger ? formatCents(ledger.outstanding_total_cents) : <span className="spinner" />}
          </div>
          <Link to="/ledger" className="btn-ghost">
            {t("home.viewPaymentLedger")}
          </Link>
        </div>

        <h3 style={{ marginTop: 24, marginBottom: 8 }}>{t("home.recentSessions")}</h3>
        {sessions === null && <div className="empty-state">{t("common.loading")}</div>}
        {sessions !== null && sessions.length === 0 && (
          <div className="empty-state">{t("home.noSessionsYet")}</div>
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
                {t("home.sessionMeta", {
                  date: formatDate(s.service_date),
                  completed: s.packages_completed,
                  assigned: s.packages_assigned,
                })}
              </div>
              <div className="mono" style={{ marginTop: 6 }}>
                {formatCents(s.expected_gross_cents)}
              </div>
            </div>
          </Link>
        ))}
      </div>

      <Link to="/sessions/new" className="fab" aria-label={t("home.startSessionAria")}>
        +
      </Link>
      <BottomNav />
    </div>
  );
}
