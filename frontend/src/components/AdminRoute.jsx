import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// UI convenience only: hides the admin page from non-admins.
// The REAL protection is on the backend (require_admin returns 403).
function AdminRoute({ children }) {
  const { isAuthenticated, isAdmin } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!isAdmin) return <Navigate to="/products" replace />;
  return children;
}

export default AdminRoute;
