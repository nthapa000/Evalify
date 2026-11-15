// TaLogin.jsx — email + password login page for TAs (accounts come from demo.env).
// On success, redirects to /ta/dashboard.

import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import useAuth from "../../hooks/useAuth";
import Button from "../../components/ui/Button";
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
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="mx-auto w-14 h-14 rounded-2xl bg-green-600 flex items-center justify-center mb-3">
            <span className="text-white text-2xl font-bold">E</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-800">TA Login</h1>
          <p className="text-gray-500 text-sm mt-1">Review flagged answers and re-evaluation requests</p>
        </div>

        {/* Form card */}
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 space-y-5">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 text-sm rounded-lg px-4 py-3">{error}</div>
          )}
          <div>
            <label htmlFor="ta-email" className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input id="ta-email" type="email" autoFocus value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="ta.cs1@evalify.local"
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-400" />
          </div>
          <div>
            <label htmlFor="ta-password" className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input id="ta-password" type="password" value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="••••••••"
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-400" />
          </div>
          {/* Demo accounts are listed in demo.env */}
          <p className="text-xs text-gray-400">
            Demo: <code className="bg-gray-100 px-1 rounded">ta.cs1@evalify.local</code> / <code className="bg-gray-100 px-1 rounded">Ta@12345</code>
          </p>
          <Button type="submit" loading={loading} className="w-full" size="lg">Sign In</Button>
        </form>

        {/* Switch to the other logins */}
        <p className="text-center text-sm text-gray-500 mt-6">
          <Link to="/login/teacher" className="text-green-600 font-medium hover:underline">Teacher Login →</Link>
          {" · "}
          <Link to="/login/student" className="text-green-600 font-medium hover:underline">Student Login →</Link>
        </p>
      </div>
    </div>
  );
}
