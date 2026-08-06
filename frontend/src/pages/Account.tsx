import { useNavigate } from "react-router-dom";
import { api, getAuthToken } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { BottomNav } from "../components/BottomNav";

export function AccountPage() {
  const { driver, logout } = useAuth();
  const navigate = useNavigate();

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
              Grátis
            </span>
          </div>
          <p className="faint" style={{ marginTop: 4 }}>
            A Rinko está gratuita, sem limites, enquanto validamos o produto — Work Report, CSV,
            Ledger, exportação em .docx e evidence continuam liberados pra todo mundo.
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
