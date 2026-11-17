// AuthShell.jsx — shared layout of the three login pages: an ink panel with the wordmark on the left,
// the form on paper on the right, and links to the other two logins under it.

import { Link } from "react-router-dom";

const LOGINS = [
  { role: "teacher", to: "/login/teacher", label: "Teacher Login" },
  { role: "student", to: "/login/student", label: "Student Login" },
  { role: "ta", to: "/login/ta", label: "TA Login" },
];

export default function AuthShell({ role, title, subtitle, children }) {
  return (
    <div className="min-h-screen grid md:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] bg-paper-100">
      {/* Ink panel: wordmark and what the product does */}
      <aside className="bg-paper-900 text-paper-100 p-10 flex flex-col justify-between">
        <p className="font-serif text-3xl font-semibold">Evalify</p>
        <div className="space-y-3 max-w-sm">
          <p className="font-serif text-2xl leading-snug text-paper-50">Handwritten answer sheets, read twice, marked once, checked by people.</p>
          <p className="text-sm text-paper-400">OMR, MCQ, numerical and written answers. Anything the system is unsure of goes to a TA.</p>
        </div>
        <p className="kicker text-paper-500">Teacher / TA / Student</p>
      </aside>

      {/* Form on paper */}
      <main className="flex items-center justify-center p-8">
        <div className="w-full max-w-sm pl-6">
          <p className="kicker mb-1">Sign in</p>
          <h1 className="text-3xl text-paper-900">{title}</h1>
          <p className="text-sm text-paper-500 mt-1 mb-6">{subtitle}</p>
          {children}
          {/* The other two logins */}
          <p className="mt-8 text-sm text-paper-500 flex gap-4">
            {LOGINS.filter((l) => l.role !== role).map((l) => (
              <Link key={l.to} to={l.to} className="underline underline-offset-4 decoration-paper-300 hover:text-paper-900">{l.label}</Link>
            ))}
          </p>
        </div>
      </main>
    </div>
  );
}

// Labelled input used by the login forms
export function Field({ id, label, ...props }) {
  return (
    <div>
      <label htmlFor={id} className="kicker block mb-1">{label}</label>
      <input id={id} {...props}
        className="w-full border-0 border-b border-paper-400 bg-transparent px-0 py-2 text-[15px] text-paper-900 placeholder-paper-400 focus:outline-none focus:border-paper-900 focus:ring-0" />
    </div>
  );
}

// Error line shown above the form
export function FormError({ children }) {
  return children ? <p role="alert" className="text-sm text-pen-600 border-l-2 border-pen-500 pl-3">{children}</p> : null;
}
