import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext.jsx";

// Wraps routes that require authentication. Preserves the intended path so we
// can return the user there after login.
export function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) return <p role="status" className="container">Loading…</p>;
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return children;
}

// Wraps admin-only routes.
export function RequireAdmin({ children }) {
  const { isAuthenticated, isAdmin, loading } = useAuth();
  const location = useLocation();

  if (loading) return <p role="status" className="container">Loading…</p>;
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (!isAdmin) return <Navigate to="/" replace />;
  return children;
}
