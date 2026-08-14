import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "../api/client";
import { formatCents, formatDate } from "../api/format";
import type { LedgerSummary } from "../api/types";
import { BottomNav } from "../components/BottomNav";
import { StatusPill } from "../components/StatusPill";

export function LedgerPage() {
  const { t } = useTranslation();
  const [ledger, setLedger] = useState<LedgerSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<LedgerSummary>("/ledger")
      .then(setLedger)
      .catch((err) => setError(err instanceof ApiError ? err.message : t("common.failedToLoad")));
  }, [t]);

  return (
    <div className="app-shell">
      <div className="top-bar">
        <h1>{t("ledger.title")}</h1>
      </div>
      <div className="screen">
        {error && <div className="error-banner">{error}</div>}

        <div className="card" style={{ background: "var(--surface-2)", textAlign: "center" }}>
          <div className="faint">{t("ledger.outstanding")}</div>
          <div className="mono" style={{ fontSize: "2rem", color: "var(--violet-glow)" }}>
            {ledger ? formatCents(ledger.outstanding_total_cents) : <span className="spinner" />}
          </div>
        </div>

        {ledger?.entries.length === 0 && (
          <div className="empty-state">{t("ledger.none")}</div>
        )}

        {ledger?.entries.map((entry) => (
          <Link
            key={entry.session_id}
            to={`/sessions/${entry.session_id}`}
            style={{ textDecoration: "none", color: "inherit" }}
          >
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <strong>{entry.carrier_name}</strong>
                <StatusPill status={entry.payment_status} />
              </div>
              <div className="faint">
                {formatDate(entry.service_date)}
                {entry.route_id ? ` · ${entry.route_id}` : ""}
              </div>
              <div className="row">
                <span className="label">{t("ledger.expected")}</span>
                <span className="mono">{formatCents(entry.expected_gross_cents)}</span>
              </div>
              <div className="row">
                <span className="label">{t("ledger.outstandingRow")}</span>
                <span className="mono">{formatCents(entry.outstanding_cents)}</span>
              </div>
            </div>
          </Link>
        ))}
      </div>
      <BottomNav />
    </div>
  );
}
