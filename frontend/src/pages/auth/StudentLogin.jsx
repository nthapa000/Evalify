// StudentLogin.jsx — roll number + password login page for students (accounts from demo.env).
// On success, redirects to /student/dashboard.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import useAuth from "../../hooks/useAuth";
import Button from "../../components/ui/Button";
import AuthShell, { Field, FormError } from "../../components/layout/AuthShell";
import { validateStudentLogin } from "../../utils/validators";

export default function StudentLogin() {
  const { loginStudent, loading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ roll_no: "", password: "" });
  const [error, setError] = useState("");

  // Validate, sign in, open the dashboard
  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validateStudentLogin(form);
    if (err) { setError(err); return; }
    setError("");
    if (await loginStudent(form)) navigate("/student/dashboard");
  };

  return (
    <AuthShell role="student" title="Student Login" subtitle="Upload answer sheets and see how they were marked.">
      <form onSubmit={handleSubmit} className="space-y-5">
        <FormError>{error}</FormError>
        <Field id="student-roll" label="Roll number" autoFocus value={form.roll_no}
          onChange={(e) => setForm({ ...form, roll_no: e.target.value.toUpperCase() })} placeholder="CS2025001" />
        <Field id="student-password" label="Password" type="password" value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="••••••••" />
        {/* Demo account (demo.env) */}
        <p className="text-xs text-paper-500 font-mono">demo: CS2025001 / Student@123</p>
        <Button type="submit" loading={loading} className="w-full" size="lg">Sign In</Button>
      </form>
    </AuthShell>
  );
}
