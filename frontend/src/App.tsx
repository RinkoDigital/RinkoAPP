import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { AuthPage } from "./pages/Auth";
import { HomePage } from "./pages/Home";
import { StartSessionPage } from "./pages/StartSession";
import { SessionDetailPage } from "./pages/SessionDetail";
import { WorkReportPage } from "./pages/WorkReport";
import { LedgerPage } from "./pages/Ledger";
import { AccountPage } from "./pages/Account";

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
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
