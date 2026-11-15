// Sidebar.jsx — left index of the role's pages, numbered like a contents page; the open page is
// marked with a red-pen rule.

import { NavLink } from "react-router-dom";
import useAuthStore from "../../store/authStore";

// One numbered entry
function SideLink({ to, label, n }) {
  return (
    <NavLink to={to} end
      className={({ isActive }) =>
        `flex items-baseline gap-3 pl-4 pr-3 py-2 text-sm border-l-2 transition-colors
         ${isActive ? "border-pen-500 text-paper-900 bg-paper-50" : "border-transparent text-paper-600 hover:text-paper-900"}`}>
      <span className="font-mono text-[11px] text-paper-400">{String(n).padStart(2, "0")}</span>
      <span>{label}</span>
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
    <aside className="w-52 bg-paper-100 border-r border-paper-300 flex flex-col py-5 flex-shrink-0">
      <p className="kicker px-4 mb-2">Contents</p>
      <nav className="flex flex-col">
        {links.map((l, i) => <SideLink key={l.to} n={i + 1} {...l} />)}
      </nav>

      {/* Subjects of the user, if any */}
      {user?.subjects?.length > 0 && (
        <div className="mt-auto px-4">
          <p className="kicker mb-1">Subjects</p>
          {user.subjects.map((s) => <p key={s} className="text-xs text-paper-600">{s}</p>)}
        </div>
      )}
    </aside>
  );
}
