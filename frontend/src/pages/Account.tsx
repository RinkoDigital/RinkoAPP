import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api, ApiError, getAuthToken } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { BottomNav } from "../components/BottomNav";

export function AccountPage() {
  const { t } = useTranslation();
  const { driver, logout } = useAuth();
  const navigate = useNavigate();
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  async function handleDeleteAccount() {
    if (!window.confirm(t("account.deleteConfirm"))) return;
    setDeleteError(null);
    setDeleting(true);
    try {
      await api.delete("/account/me");
      logout();
      navigate("/auth", { replace: true });
    } catch (err) {
      setDeleteError(err instanceof ApiError ? err.message : t("common.failedToLoad"));
      setDeleting(false);
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
        a.download = "shiftproof_work_sessions.csv";
        a.click();
        URL.revokeObjectURL(url);
      });
  }

  return (
    <div className="app-shell">
      <div className="top-bar">
        <h1>{t("account.title")}</h1>
      </div>
      <div className="screen">
        <div className="card">
          <strong>{driver?.name}</strong>
          <div className="faint">{driver?.email}</div>
          {driver && !driver.email_verified && (
            <div className="faint" style={{ marginTop: 6, color: "var(--sakura)" }}>
              {t("account.emailUnverified")}
            </div>
          )}
        </div>

        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ margin: 0 }}>{t("account.plan")}</h3>
            <span className="pill pill-good" style={{ textTransform: "uppercase" }}>
              {t("account.free")}
            </span>
          </div>
          <p className="faint" style={{ marginTop: 4 }}>
            {t("account.planDescription")}
          </p>
        </div>

        <div className="card">
          <h3 style={{ marginTop: 0 }}>{t("account.dataTitle")}</h3>
          <button className="btn btn-secondary" onClick={handleExportCsv}>
            {t("account.exportCsv")}
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
          {t("account.logout")}
        </button>

        {deleteError && <div className="error-banner">{deleteError}</div>}
        <button
          className="btn-ghost"
          style={{ color: "var(--bad)", marginTop: 10 }}
          onClick={handleDeleteAccount}
          disabled={deleting}
        >
          {deleting ? <span className="spinner" /> : t("account.deleteAccount")}
        </button>
      </div>
      <BottomNav />
    </div>
  );
}
