import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "@/features/auth/AuthContext";
import Assistant from "@/features/assistant/pages/Assistant";
import ForgotPassword from "@/features/auth/pages/ForgotPassword";
import Login from "@/features/auth/pages/Login";
import Profile from "@/features/auth/pages/Profile";
import Register from "@/features/auth/pages/Register";
import ResetPassword from "@/features/auth/pages/ResetPassword";
import VerifyEmail from "@/features/auth/pages/VerifyEmail";
import Budgets from "@/features/budgets/pages/Budgets";
import Investments from "@/features/investments/pages/Investments";
import Landing from "@/features/marketing/pages/Landing";
import Legal from "@/features/marketing/pages/Legal";
import LoanDetail from "@/features/loans/pages/LoanDetail";
import Loans from "@/features/loans/pages/Loans";
import Marketplace from "@/features/marketplace/pages/Marketplace";
import Offers from "@/features/marketplace/pages/Offers";
import Notifications from "@/features/notifications/pages/Notifications";
import Payments from "@/features/payments/pages/Payments";
import Dashboard from "@/features/wallet/pages/Dashboard";
import Wallet from "@/features/wallet/pages/Wallet";
import AppLayout from "@/app/layout/AppLayout";
import { ENABLE_ASSISTANT } from "@/shared/lib/features";

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading">Cargando…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function ProfileOnly({
  allow,
  children,
}: {
  allow: string[];
  children: React.ReactNode;
}) {
  const { activeProfile } = useAuth();
  if (activeProfile && !allow.includes(activeProfile)) {
    return <Navigate to="/dashboard" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  const { user, loading } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={
          user && !loading ? <Navigate to="/dashboard" replace /> : <Login />
        }
      />
      <Route
        path="/registro"
        element={
          user && !loading ? <Navigate to="/dashboard" replace /> : <Register />
        }
      />
      <Route path="/recuperar" element={<ForgotPassword />} />
      <Route path="/restablecer" element={<ResetPassword />} />
      <Route path="/verificar" element={<VerifyEmail />} />
      <Route path="/" element={<Landing />} />
      <Route path="/legal" element={<Legal />} />
      <Route
        element={
          <Protected>
            <AppLayout />
          </Protected>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/billetera" element={<Wallet />} />
        <Route
          path="/pagos"
          element={
            <ProfileOnly allow={["borrower", "lender"]}>
              <Payments />
            </ProfileOnly>
          }
        />
        <Route
          path="/presupuestos"
          element={
            <ProfileOnly allow={["borrower", "lender"]}>
              <Budgets />
            </ProfileOnly>
          }
        />
        <Route
          path="/marketplace"
          element={
            <ProfileOnly allow={["borrower"]}>
              <Marketplace />
            </ProfileOnly>
          }
        />
        <Route
          path="/ofertas"
          element={
            <ProfileOnly allow={["lender"]}>
              <Offers />
            </ProfileOnly>
          }
        />
        <Route
          path="/prestamos"
          element={
            <ProfileOnly allow={["borrower", "lender"]}>
              <Loans />
            </ProfileOnly>
          }
        />
        <Route
          path="/prestamos/:loanId"
          element={
            <ProfileOnly allow={["borrower", "lender"]}>
              <LoanDetail />
            </ProfileOnly>
          }
        />
        <Route
          path="/inversiones"
          element={
            <ProfileOnly allow={["investor"]}>
              <Investments />
            </ProfileOnly>
          }
        />
        <Route path="/notificaciones" element={<Notifications />} />
        {ENABLE_ASSISTANT && (
          <Route path="/asistente" element={<Assistant />} />
        )}
        <Route path="/perfil" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
