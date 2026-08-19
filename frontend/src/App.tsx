import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "@/components/shared/ProtectedRoute";
import DashboardPage from "@/routes/DashboardPage";
import ForgotPasswordPage from "@/routes/ForgotPasswordPage";
import LoginPage from "@/routes/LoginPage";
import RegisterPage from "@/routes/RegisterPage";
import ResetPasswordPage from "@/routes/ResetPasswordPage";
import TeamPage from "@/routes/TeamPage";
import VerifyEmailPage from "@/routes/VerifyEmailPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/organizations/:orgId/team" element={<TeamPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
