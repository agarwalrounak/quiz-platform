import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext.jsx";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || "/";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);

  // If we were redirected here by an expired session, explain why (once).
  useEffect(() => {
    if (sessionStorage.getItem("quiz.sessionExpired")) {
      sessionStorage.removeItem("quiz.sessionExpired");
      setNotice("Your session expired. Please log in again.");
    }
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(
        err.response?.status === 401
          ? "Invalid username or password."
          : "Login failed. Please try again."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="container narrow">
      <h1>Log in</h1>
      <form onSubmit={onSubmit} noValidate>
        {notice && !error && (
          <p role="status" className="hint notice">
            {notice}
          </p>
        )}
        {error && (
          <p role="alert" className="status-error">
            {error}
          </p>
        )}
        <div className="field">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            name="username"
            autoComplete="username"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button type="submit" disabled={busy}>
          {busy ? "Logging in…" : "Log in"}
        </button>
      </form>
      <p>
        No account? <Link to="/register">Register</Link>
      </p>
    </main>
  );
}
