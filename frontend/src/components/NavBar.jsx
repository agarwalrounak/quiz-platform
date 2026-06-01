import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

// NavLink sets aria-current="page" on the active route automatically.
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
              <NavLink to="/history">My attempts</NavLink>
            </li>
          )}
          {isAdmin && (
            <li>
              <NavLink to="/admin/questions">Question bank</NavLink>
            </li>
          )}
          {isAdmin && (
            <li>
              <NavLink to="/admin/review">Review queue</NavLink>
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
              <NavLink to="/login">Log in</NavLink>
            </li>
          )}
        </ul>
      </nav>
    </header>
  );
}
