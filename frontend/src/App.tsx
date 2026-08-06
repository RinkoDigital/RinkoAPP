import { useEffect } from "react";
import { App as CapacitorApp } from "@capacitor/app";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { AuthPage } from "./pages/Auth";
import { HomePage } from "./pages/Home";
import { StartSessionPage } from "./pages/StartSession";
import { SessionDetailPage } from "./pages/SessionDetail";
import { WorkReportPage } from "./pages/WorkReport";
import { LedgerPage } from "./pages/Ledger";
import { AccountPage } from "./pages/Account";
import { ShareAttachPage } from "./pages/ShareAttach";
import { consumePendingShare, onShareReceived } from "./native/shareTarget";

function RequireAuth({ children }: { children: React.ReactElement }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/auth" replace />;
  return children;
}

function RedirectIfAuthed({ children }: { children: React.ReactElement }) {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) return <Navigate to="/" replace />;
  return children;
}

/** Owns reading whatever the OS Share Sheet handed us and is the single
 * place that consumes it, so it's never read twice. Three triggers, since
 * Android and iOS hand off a pending share differently:
 *  - app launch/login (cold start, or a share that arrived while logged out)
 *  - Android's onNewIntent while already open (native "shareReceived" event)
 *  - app foregrounded (covers iOS, which has no equivalent live event —
 *    its Share Extension runs in a separate process and just drops a file
 *    in the shared App Group container for the main app to notice)
 */
function ShareGate() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) return;

    const check = () => {
      consumePendingShare().then((item) => {
        if (item) navigate("/share", { state: { item } });
      });
    };

    check();
    const removeShareListener = onShareReceived((item) => navigate("/share", { state: { item } }));
    const resumeListenerPromise = CapacitorApp.addListener("appStateChange", (state) => {
      if (state.isActive) check();
    });

    return () => {
      removeShareListener();
      resumeListenerPromise.then((h) => h.remove()).catch(() => {});
    };
  }, [isAuthenticated, navigate]);

  return null;
}

function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/auth"
        element={
          <RedirectIfAuthed>
            <AuthPage />
          </RedirectIfAuthed>
        }
      />
      <Route
        path="/"
        element={
          <RequireAuth>
            <HomePage />
          </RequireAuth>
        }
      />
      <Route
        path="/sessions/new"
        element={
          <RequireAuth>
            <StartSessionPage />
          </RequireAuth>
        }
      />
      <Route
        path="/sessions/:sessionId"
        element={
          <RequireAuth>
            <SessionDetailPage />
          </RequireAuth>
        }
      />
      <Route
        path="/sessions/:sessionId/report"
        element={
          <RequireAuth>
            <WorkReportPage />
          </RequireAuth>
        }
      />
      <Route
        path="/ledger"
        element={
          <RequireAuth>
            <LedgerPage />
          </RequireAuth>
        }
      />
      <Route
        path="/account"
        element={
          <RequireAuth>
            <AccountPage />
          </RequireAuth>
        }
      />
      <Route
        path="/share"
        element={
          <RequireAuth>
            <ShareAttachPage />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ShareGate />
      <AppRoutes />
    </AuthProvider>
  );
}
