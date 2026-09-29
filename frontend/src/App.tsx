import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { CookieConsent } from "@/components/shared/CookieConsent";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";
const AccountPage = lazy(() => import("@/routes/AccountPage"));
const AdminPage = lazy(() => import("@/routes/AdminPage"));
const AiToolsPage = lazy(() => import("@/routes/AiToolsPage"));
const AnalyticsPage = lazy(() => import("@/routes/AnalyticsPage"));
const AcceptInvitePage = lazy(() => import("@/routes/AcceptInvitePage"));
const BillingReturnPage = lazy(() => import("@/routes/BillingReturnPage"));
const BillingPage = lazy(() => import("@/routes/BillingPage"));
const ChatPage = lazy(() => import("@/routes/ChatPage"));
const DashboardPage = lazy(() => import("@/routes/DashboardPage"));
const DocumentsPage = lazy(() => import("@/routes/DocumentsPage"));
const ForgotPasswordPage = lazy(() => import("@/routes/ForgotPasswordPage"));
const LandingPage = lazy(() => import("@/routes/LandingPage"));
const LoginPage = lazy(() => import("@/routes/LoginPage"));
const ModelsPage = lazy(() => import("@/routes/ModelsPage"));
const RegisterPage = lazy(() => import("@/routes/RegisterPage"));
const ResetPasswordPage = lazy(() => import("@/routes/ResetPasswordPage"));
const SharedDocumentPage = lazy(() => import("@/routes/SharedDocumentPage"));
const TeamPage = lazy(() => import("@/routes/TeamPage"));
const VerifyEmailPage = lazy(() => import("@/routes/VerifyEmailPage"));
const PrivacyPage = lazy(() =>
  import("@/routes/LegalPages").then((module) => ({
    default: module.PrivacyPage,
  })),
);
const TermsPage = lazy(() =>
  import("@/routes/LegalPages").then((module) => ({
    default: module.TermsPage,
  })),
);

export default function App() {
  return (
    <>
      <Suspense
        fallback={<p className="p-8 text-sm text-neutral-400">Yükleniyor…</p>}
      >
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
        <Route path="/accept-invite" element={<AcceptInvitePage />} />

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
          <Route path="/billing" element={<BillingReturnPage />} />
          <Route
            path="/organizations/:orgId/analytics"
            element={<AnalyticsPage />}
          />
          <Route path="/organizations/:orgId/models" element={<ModelsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
      <CookieConsent />
    </>
  );
}
