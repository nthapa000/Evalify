// TeacherLogin.jsx — email + password login page for teachers (accounts from demo.env).
// On success, redirects to /teacher/dashboard.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import useAuth from "../../hooks/useAuth";
import Button from "../../components/ui/Button";
import AuthShell, { Field, FormError } from "../../components/layout/AuthShell";
import { validateTeacherLogin } from "../../utils/validators";

export default function TeacherLogin() {
  const { loginTeacher, loading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");

  // Validate, sign in, open the dashboard
  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validateTeacherLogin(form);
    if (err) { setError(err); return; }
    setError("");
    if (await loginTeacher(form)) navigate("/teacher/dashboard");
  };

  return (
    <AuthShell role="teacher" title="Teacher Login" subtitle="Create papers, see results, calibrate marking.">
      <form onSubmit={handleSubmit} className="space-y-5">
        <FormError>{error}</FormError>
        <Field id="teacher-email" label="Email" type="email" autoFocus value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="teacher@evalify.local" />
        <Field id="teacher-password" label="Password" type="password" value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="••••••••" />
        {/* Demo account (demo.env) */}
        <p className="text-xs text-paper-500 font-mono">demo: teacher@evalify.local / Teacher@123</p>
        <Button type="submit" loading={loading} className="w-full" size="lg">Sign In</Button>
      </form>
    </AuthShell>
  );
}
