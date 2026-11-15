// Navbar.jsx — top bar: serif wordmark, the user's name and role, sign out.

import { Link, useNavigate } from "react-router-dom";
import useAuthStore from "../../store/authStore";

const ROLE_LABEL = { teacher: "Teacher", ta: "TA", student: "Student" };

export default function Navbar() {
  const { user, clearAuth } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    clearAuth();
    // Back to the login page of the role that signed out
    navigate({ teacher: "/login/teacher", ta: "/login/ta" }[user?.role] ?? "/login/student");
  };

  return (
    <header className="h-14 bg-paper-50 border-b border-paper-900 flex items-center justify-between px-6 flex-shrink-0 z-10">
      {/* Wordmark */}
      <Link to="/" className="flex items-baseline gap-2">
        <span className="font-serif text-xl font-semibold text-paper-900">Evalify</span>
        <span className="kicker hidden sm:inline">answer sheets, marked</span>
      </Link>

      {/* User + sign out */}
      {user && (
        <div className="flex items-center gap-5">
          <div className="text-right hidden sm:block leading-tight">
            <p className="text-sm text-paper-900">{user.name}</p>
            <p className="kicker">{ROLE_LABEL[user.role] ?? user.role}{user.roll_no ? ` / ${user.roll_no}` : ""}</p>
          </div>
          <button onClick={handleLogout} className="text-sm text-paper-600 underline underline-offset-4 decoration-paper-300 hover:text-pen-600 hover:decoration-pen-400">
            Sign out
          </button>
        </div>
      )}
    </header>
  );
}
