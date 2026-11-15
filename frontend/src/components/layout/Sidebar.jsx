// Sidebar.jsx — left navigation panel with role-based links.

import { NavLink } from "react-router-dom";
import useAuthStore from "../../store/authStore";

// Nav link, highlighted when its route is active
function SideLink({ to, label }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-colors
         ${isActive ? "bg-green-50 text-green-700 border-l-2 border-green-600" : "text-gray-600 hover:bg-gray-100 hover:text-gray-800"}`
      }
    >
      {label}
    </NavLink>
  );
}

// Links shown per role
const TEACHER_LINKS = [
  { to: "/teacher/dashboard",       label: "Dashboard" },
  { to: "/teacher/papers/create",   label: "Create Paper" },
];

const STUDENT_LINKS = [
  { to: "/student/dashboard",       label: "Dashboard" },
];

// TA: one page with the two review tabs
const TA_LINKS = [
  { to: "/ta/dashboard",            label: "Review queue" },
];

export default function Sidebar() {
  const { user } = useAuthStore();
  const links = { teacher: TEACHER_LINKS, ta: TA_LINKS }[user?.role] ?? STUDENT_LINKS;

  return (
    <aside className="w-56 bg-white border-r border-gray-200 flex flex-col py-4 flex-shrink-0">
      <nav className="flex flex-col gap-1 px-2">
        {links.map((l) => (
          <SideLink key={l.to} {...l} />
        ))}
      </nav>

      {/* Current role at the bottom */}
      <div className="mt-auto px-4 pb-2">
        <p className="text-xs text-gray-400 uppercase tracking-wide font-medium capitalize">
          {user?.role ?? ""}
        </p>
      </div>
    </aside>
  );
}
