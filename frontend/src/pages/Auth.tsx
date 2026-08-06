import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";
import { KitsuneMask } from "../components/KitsuneMask";

export function AuthPage() {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login, signup } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await signup(name, email, password);
      }
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <div
        className="screen"
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          minHeight: "100%",
          position: "relative",
        }}
      >
        <div
          className="glow"
          aria-hidden="true"
          style={{ top: -140, left: "50%", transform: "translateX(-50%)", width: 320, height: 320 }}
        />
        <div className="petal" aria-hidden="true" style={{ top: 20, left: "26%" }} />
        <div
          className="petal"
          aria-hidden="true"
          style={{ top: 44, right: "24%", transform: "rotate(-20deg)", opacity: 0.35 }}
        />

        <div style={{ textAlign: "center", marginBottom: 36, position: "relative", zIndex: 1 }}>
          <div style={{ display: "flex", justifyContent: "center", marginBottom: 10 }}>
            <KitsuneMask />
          </div>
          <div className="wordmark" style={{ fontSize: "2rem", color: "var(--crimson-glow)" }}>
            RINKO
          </div>
          <div className="faint" style={{ letterSpacing: "0.08em" }}>
            Your routes. Your work. Your records.
          </div>
        </div>

        <div className="card" style={{ position: "relative", zIndex: 1 }}>
          <div style={{ display: "flex", marginBottom: 18, borderBottom: "1px solid var(--line)" }}>
            <button
              type="button"
              onClick={() => setMode("login")}
              className="btn-ghost"
              style={{
                flex: 1,
                borderBottom: mode === "login" ? "2px solid var(--crimson)" : "2px solid transparent",
                color: mode === "login" ? "var(--text)" : "var(--text-faint)",
                fontWeight: 600,
              }}
            >
              Entrar
            </button>
            <button
              type="button"
              onClick={() => setMode("signup")}
              className="btn-ghost"
              style={{
                flex: 1,
                borderBottom: mode === "signup" ? "2px solid var(--crimson)" : "2px solid transparent",
                color: mode === "signup" ? "var(--text)" : "var(--text-faint)",
                fontWeight: 600,
              }}
            >
              Criar conta
            </button>
          </div>

          {error && <div className="error-banner">{error}</div>}

          <form onSubmit={handleSubmit}>
            {mode === "signup" && (
              <div className="field">
                <label htmlFor="name">Nome</label>
                <input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
            )}
            <div className="field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="password">Senha</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <span className="spinner" /> : mode === "login" ? "Entrar" : "Criar conta"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
