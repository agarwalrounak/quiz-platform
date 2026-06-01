import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext.jsx";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [errors, setErrors] = useState(null);
  const [busy, setBusy] = useState(false);

  function update(field) {
    return (e) => setForm({ ...form, [field]: e.target.value });
  }

  async function onSubmit(e) {
    e.preventDefault();
    setErrors(null);
    setBusy(true);
    try {
      await register(form.username, form.email, form.password);
      navigate("/", { replace: true });
    } catch (err) {
      const data = err.response?.data;
      // DRF returns field-keyed arrays of messages.
      setErrors(
        data && typeof data === "object"
          ? Object.entries(data).map(([k, v]) => `${k}: ${[].concat(v).join(" ")}`)
          : ["Registration failed. Please try again."]
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="container narrow">
      <h1>Create account</h1>
      <form onSubmit={onSubmit} noValidate>
        {errors && (
          <ul role="alert" className="status-error">
            {errors.map((msg) => (
              <li key={msg}>{msg}</li>
            ))}
          </ul>
        )}
        <div className="field">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            autoComplete="username"
            required
            value={form.username}
            onChange={update("username")}
          />
        </div>
        <div className="field">
          <label htmlFor="email">Email (optional)</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={form.email}
            onChange={update("email")}
          />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            value={form.password}
            onChange={update("password")}
          />
        </div>
        <button type="submit" disabled={busy}>
          {busy ? "Creating…" : "Create account"}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </main>
  );
}
