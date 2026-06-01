import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

export default function NavBar() {
  const { isAuthenticated, isAdmin, user, logout } = useAuth();
  const navigate = useNavigate();

  function onLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="navbar">
      <nav className="container nav-inner" aria-label="Primary">
        <Link to="/" className="brand">
          Quiz Platform
        </Link>
        <ul className="nav-links">
          {isAuthenticated && (
            <li>
              <Link to="/history">My attempts</Link>
            </li>
          )}
          {isAdmin && (
            <li>
              <Link to="/admin/questions">Question bank</Link>
            </li>
          )}
          {isAuthenticated ? (
            <>
              <li className="nav-user">
                {user.username}
                {isAdmin && <span className="badge">admin</span>}
              </li>
              <li>
                <button type="button" className="link-btn" onClick={onLogout}>
                  Log out
                </button>
              </li>
            </>
          ) : (
            <li>
              <Link to="/login">Log in</Link>
            </li>
          )}
        </ul>
      </nav>
    </header>
  );
}
