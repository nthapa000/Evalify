// TaLogin.jsx — email + password login page for TAs (accounts come from demo.env).
// On success, redirects to /ta/dashboard.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import useAuth from "../../hooks/useAuth";
import Button from "../../components/ui/Button";
import AuthShell, { Field, FormError } from "../../components/layout/AuthShell";
import { validateTeacherLogin } from "../../utils/validators";

export default function TaLogin() {
  const { loginTa, loading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");

  // Same checks as the teacher login (email + password), then sign in
  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validateTeacherLogin(form);
    if (err) { setError(err); return; }
    setError("");
    if (await loginTa(form)) navigate("/ta/dashboard");
  };

  return (
    <AuthShell role="ta" title="TA Login" subtitle="Review flagged answers and re-evaluation requests.">
      <form onSubmit={handleSubmit} className="space-y-5">
        <FormError>{error}</FormError>
        <Field id="ta-email" label="Email" type="email" autoFocus value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="ta.cs1@evalify.local" />
        <Field id="ta-password" label="Password" type="password" value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="••••••••" />
        {/* Demo account (demo.env) */}
        <p className="text-xs text-paper-500 font-mono">demo: ta.cs1@evalify.local / Ta@12345</p>
        <Button type="submit" loading={loading} className="w-full" size="lg">Sign In</Button>
      </form>
    </AuthShell>
  );
}
