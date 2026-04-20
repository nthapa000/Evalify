// Navbar.jsx — top navigation bar.
// Shows app name, user info, and logout button.
// Content adapts based on the logged-in role (teacher vs student).

import { Link, useNavigate } from "react-router-dom";
import useAuthStore from "../../store/authStore";

export default function Navbar() {
  const { user, clearAuth } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    clearAuth();
    navigate(user?.role === "teacher" ? "/login/teacher" : "/login/student");
  };

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 flex-shrink-0 z-10">
      {/* Logo */}
      <Link to="/" className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
          <span className="text-white text-sm font-bold">E</span>
        </div>
        <span className="text-lg font-bold text-gray-800">Evalify</span>
      </Link>

      {/* User info + logout */}
      {user && (
        <div className="flex items-center gap-4">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-gray-800">{user.name}</p>
            <p className="text-xs text-gray-400 capitalize">{user.role}</p>
          </div>
          {/* Avatar circle with initials */}
          <div className="w-9 h-9 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-sm font-semibold">
            {user.name?.[0]?.toUpperCase() ?? "?"}
          </div>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-500 hover:text-red-500 transition-colors"
          >
            Sign out
          </button>
        </div>
      )}
    </header>
  );
}
