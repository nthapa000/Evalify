// StudentLogin.jsx — roll number + password login for students.
// On success, redirects to /student/dashboard.

import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import useAuth from "../../hooks/useAuth";
import Button from "../../components/ui/Button";
import { validateStudentLogin } from "../../utils/validators";

export default function StudentLogin() {
  const { loginStudent, loading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm]   = useState({ roll_no: "", password: "" });
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validateStudentLogin(form);
    if (err) { setError(err); return; }
    setError("");
    const ok = await loginStudent(form);
    if (ok) navigate("/student/dashboard");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="mx-auto w-14 h-14 rounded-2xl bg-green-600 flex items-center justify-center mb-3">
            <span className="text-white text-2xl font-bold">E</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Student Login</h1>
          <p className="text-gray-500 text-sm mt-1">View your exams and results</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 space-y-5">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 text-sm rounded-lg px-4 py-3">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Roll Number</label>
            <input
              type="text"
              autoFocus
              value={form.roll_no}
              onChange={(e) => setForm({ ...form, roll_no: e.target.value.toUpperCase() })}
              placeholder="CS2025001"
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-400 uppercase"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit(e)}
              placeholder="••••••••"
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-400"
            />
          </div>

          <p className="text-xs text-gray-400">
            Demo: <code className="bg-gray-100 px-1 rounded">CS2025001</code> / <code className="bg-gray-100 px-1 rounded">Student@123</code>
          </p>

          <Button onClick={handleSubmit} loading={loading} className="w-full" size="lg">
            Sign In
          </Button>
        </div>

        <p className="text-center text-sm text-gray-500 mt-6">
          Are you a teacher?{" "}
          <Link to="/login/teacher" className="text-green-600 font-medium hover:underline">
            Teacher Login →
          </Link>
        </p>
      </div>
    </div>
  );
}
