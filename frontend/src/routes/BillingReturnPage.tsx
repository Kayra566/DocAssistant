import { Navigate, useSearchParams } from "react-router-dom";

export default function BillingReturnPage() {
  const [params] = useSearchParams();
  const orgId = sessionStorage.getItem("docassistant-billing-org");

  if (!orgId) return <Navigate to="/dashboard" replace />;

  const query = new URLSearchParams();
  for (const key of ["status", "session_id", "customer"]) {
    const value = params.get(key);
    if (value) query.set(key, value);
  }
  return (
    <Navigate
      to={`/organizations/${orgId}/billing${query.size ? `?${query}` : ""}`}
      replace
    />
  );
}
