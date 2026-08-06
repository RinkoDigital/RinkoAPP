import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, getAuthToken } from "../api/client";
import type { PlanInfo } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { BottomNav } from "../components/BottomNav";

export function AccountPage() {
  const { driver, logout } = useAuth();
  const navigate = useNavigate();
  const [plan, setPlan] = useState<PlanInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [switching, setSwitching] = useState(false);

  function loadPlan() {
    api
      .get<PlanInfo>("/account/plan")
      .then(setPlan)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load plan"));
  }

  useEffect(loadPlan, []);

  async function togglePlan() {
    if (!plan) return;
    setSwitching(true);
    setError(null);
    try {
      const next = plan.plan === "free" ? "pro" : "free";
      const updated = await api.post<PlanInfo>("/account/plan", { plan: next });
      setPlan(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to switch plan");
    } finally {
      setSwitching(false);
    }
  }

  function handleExportCsv() {
    const token = getAuthToken();
    // The browser can't send an Authorization header on a plain navigation,
    // so fetch the CSV and hand the browser a blob URL to download instead.
    fetch(api.downloadUrl("/sessions/export.csv"), {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "rinko_work_sessions.csv";
        a.click();
        URL.revokeObjectURL(url);
      });
  }

  return (
    <div className="app-shell">
      <div className="top-bar">
        <h1>Perfil</h1>
      </div>
      <div className="screen">
        {error && <div className="error-banner">{error}</div>}

        <div className="card">
          <strong>{driver?.name}</strong>
          <div className="faint">{driver?.email}</div>
          {driver && !driver.email_verified && (
            <div className="faint" style={{ marginTop: 6, color: "var(--sakura)" }}>
              Email ainda não verificado
            </div>
          )}
        </div>

        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ margin: 0 }}>Plano</h3>
            <span className="pill pill-good" style={{ textTransform: "uppercase" }}>
              {plan?.plan ?? "…"}
            </span>
          </div>
          <ul style={{ paddingLeft: 18, color: "var(--text-muted)", fontSize: "0.88rem" }}>
            <li>Work Report (JSON), CSV e Ledger: sempre grátis</li>
            <li>
              Exportação .docx:{" "}
              {plan?.docx_export ? "liberada" : <span className="locked-badge">Pro</span>}
            </li>
            <li>
              Evidence por sessão:{" "}
              {plan?.evidence_per_session_limit === null
                ? "ilimitado"
                : `até ${plan?.evidence_per_session_limit ?? "…"}`}
            </li>
          </ul>
          <button className="btn btn-secondary" onClick={togglePlan} disabled={switching || !plan}>
            {switching ? (
              <span className="spinner" />
            ) : plan?.plan === "free" ? (
              "Fazer upgrade para Pro"
            ) : (
              "Voltar para Free"
            )}
          </button>
          <p className="faint" style={{ marginTop: 10 }}>
            Sem billing real ainda — isso troca a flag do plano manualmente, como placeholder até
            existir um provedor de pagamento.
          </p>
        </div>

        <div className="card">
          <h3 style={{ marginTop: 0 }}>Seus dados, sem lock-in</h3>
          <button className="btn btn-secondary" onClick={handleExportCsv}>
            Exportar sessões (.csv)
          </button>
        </div>

        <button
          className="btn btn-secondary"
          style={{ borderColor: "var(--bad)", color: "var(--bad)" }}
          onClick={() => {
            logout();
            navigate("/auth", { replace: true });
          }}
        >
          Sair
        </button>
      </div>
      <BottomNav />
    </div>
  );
}
