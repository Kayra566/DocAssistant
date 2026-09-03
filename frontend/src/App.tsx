import { Navigate, Route, Routes } from "react-router-dom";

import { CookieConsent } from "@/components/shared/CookieConsent";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";
import AccountPage from "@/routes/AccountPage";
import AdminPage from "@/routes/AdminPage";
import AiToolsPage from "@/routes/AiToolsPage";
import AnalyticsPage from "@/routes/AnalyticsPage";
import BillingPage from "@/routes/BillingPage";
import ChatPage from "@/routes/ChatPage";
import DashboardPage from "@/routes/DashboardPage";
import DocumentsPage from "@/routes/DocumentsPage";
import ForgotPasswordPage from "@/routes/ForgotPasswordPage";
import LandingPage from "@/routes/LandingPage";
import { PrivacyPage, TermsPage } from "@/routes/LegalPages";
import LoginPage from "@/routes/LoginPage";
import RegisterPage from "@/routes/RegisterPage";
import ResetPasswordPage from "@/routes/ResetPasswordPage";
import SharedDocumentPage from "@/routes/SharedDocumentPage";
import TeamPage from "@/routes/TeamPage";
import VerifyEmailPage from "@/routes/VerifyEmailPage";

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/share/:token" element={<SharedDocumentPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/terms" element={<TermsPage />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/account" element={<AccountPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route
            path="/organizations/:orgId/documents"
            element={<DocumentsPage />}
          />
          <Route
            path="/organizations/:orgId/documents/:docId/chat"
            element={<ChatPage />}
          />
          <Route
            path="/organizations/:orgId/documents/:docId/ai"
            element={<AiToolsPage />}
          />
          <Route path="/organizations/:orgId/team" element={<TeamPage />} />
          <Route path="/organizations/:orgId/billing" element={<BillingPage />} />
          <Route
            path="/organizations/:orgId/analytics"
            element={<AnalyticsPage />}
          />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
      <CookieConsent />
    </>
  );
}
