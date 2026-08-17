import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import logo from "../assets/logo.png";
import { useAuth } from "../context/AuthContext";

export default function Signup() {
  const [form, setForm] = useState({ name: "", email: "", password: "", grade: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { signup } = useAuth();
  const navigate = useNavigate();

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await signup({
        name: form.name,
        email: form.email,
        password: form.password,
        grade: form.grade || null,
      });
      navigate("/");
    } catch (err) {
      setError(err.message || "Could not sign up.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <img src={logo} alt="Bodhi" className="logo" />
        <h1>Create your account</h1>
        <p className="tagline">Your book. Your language. Your understanding.</p>
        {error && <div className="form-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="name">Name</label>
            <input id="name" value={form.name} onChange={(e) => update("name", e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="signup-email">Email</label>
            <input
              id="signup-email"
              type="email"
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="signup-password">Password</label>
            <input
              id="signup-password"
              type="password"
              minLength={8}
              value={form.password}
              onChange={(e) => update("password", e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="grade">Grade (optional)</label>
            <input id="grade" value={form.grade} onChange={(e) => update("grade", e.target.value)} placeholder="e.g. 10" />
          </div>
          <button className="btn btn-primary" style={{ width: "100%" }} disabled={busy} type="submit">
            {busy ? "Creating account…" : "Sign up"}
          </button>
        </form>
        <div className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </div>
      </div>
    </div>
  );
}
