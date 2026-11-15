// App.jsx — root router with full page routes and role-based route guards.
// ProtectedRoute redirects unauthenticated or wrong-role users to the right login.

import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import useAuthStore from "./store/authStore";
import ToastContainer from "./components/ui/Toast";

// Auth pages
import TeacherLogin from "./pages/auth/TeacherLogin";
import StudentLogin from "./pages/auth/StudentLogin";
import TaLogin from "./pages/auth/TaLogin";

// Teacher pages
import TeacherDashboard from "./pages/teacher/Dashboard";
import CreatePaper from "./pages/teacher/CreatePaper";
import PaperResults from "./pages/teacher/PaperResults";
import PaperView from "./pages/teacher/PaperView";

// Student pages
import StudentDashboard from "./pages/student/Dashboard";
import SubjectPage from "./pages/student/SubjectPage";
import Submission from "./pages/student/Submission";
import Result from "./pages/student/Result";

// TA pages
import TaDashboard from "./pages/ta/Dashboard";
import TaReview from "./pages/ta/Review";

// ── Route guard components ────────────────────────────────────────────────────

// Home page of each role (teacher, TA, student)
const HOME = { teacher: "/teacher/dashboard", ta: "/ta/dashboard", student: "/student/dashboard" };
const homeFor = (role) => HOME[role] ?? "/student/dashboard";

// Redirects unauthenticated users to the given loginPath
function ProtectedRoute({ children, requiredRole, loginPath }) {
  const { token, user } = useAuthStore();
  const location = useLocation();

  if (!token) {
    // Preserve the intended destination so we can redirect back after login
    return <Navigate to={loginPath} state={{ from: location }} replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    // Logged in with the wrong role — send to their own home
    return <Navigate to={homeFor(user?.role)} replace />;
  }

  return children;
}

// Redirects already-logged-in users away from login pages
function PublicOnlyRoute({ children }) {
  const { token, user } = useAuthStore();
  if (token) {
    return <Navigate to={homeFor(user?.role)} replace />;
  }
  return children;
}

// ── Root redirect ─────────────────────────────────────────────────────────────
function RootRedirect() {
  const { token, user } = useAuthStore();
  if (!token) return <Navigate to="/login/teacher" replace />;
  return <Navigate to={homeFor(user?.role)} replace />;
}

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <>
      {/* Global toast notifications rendered on top of all pages */}
      <ToastContainer />

      <Routes>
        {/* Root */}
        <Route path="/" element={<RootRedirect />} />

        {/* Auth routes — redirect away if already logged in */}
        <Route path="/login/teacher" element={<PublicOnlyRoute><TeacherLogin /></PublicOnlyRoute>} />
        <Route path="/login/student" element={<PublicOnlyRoute><StudentLogin /></PublicOnlyRoute>} />
        <Route path="/login/ta" element={<PublicOnlyRoute><TaLogin /></PublicOnlyRoute>} />

        {/* Teacher routes */}
        <Route path="/teacher/dashboard" element={<ProtectedRoute requiredRole="teacher" loginPath="/login/teacher"><TeacherDashboard /></ProtectedRoute>} />
        <Route path="/teacher/papers/create" element={<ProtectedRoute requiredRole="teacher" loginPath="/login/teacher"><CreatePaper /></ProtectedRoute>} />
        <Route path="/teacher/papers/:paperId/view" element={<ProtectedRoute requiredRole="teacher" loginPath="/login/teacher"><PaperView /></ProtectedRoute>} />
        <Route path="/teacher/papers/:paperId/results" element={<ProtectedRoute requiredRole="teacher" loginPath="/login/teacher"><PaperResults /></ProtectedRoute>} />

        {/* Student routes */}
        <Route path="/student/dashboard" element={<ProtectedRoute requiredRole="student" loginPath="/login/student"><StudentDashboard /></ProtectedRoute>} />
        <Route path="/student/subjects/:subject" element={<ProtectedRoute requiredRole="student" loginPath="/login/student"><SubjectPage /></ProtectedRoute>} />
        <Route path="/student/submit/:paperId" element={<ProtectedRoute requiredRole="student" loginPath="/login/student"><Submission /></ProtectedRoute>} />
        <Route path="/student/results/:submissionId" element={<ProtectedRoute requiredRole="student" loginPath="/login/student"><Result /></ProtectedRoute>} />

        {/* TA routes: review queue (two tabs) and one answer sheet */}
        <Route path="/ta/dashboard" element={<ProtectedRoute requiredRole="ta" loginPath="/login/ta"><TaDashboard /></ProtectedRoute>} />
        <Route path="/ta/review/:submissionId" element={<ProtectedRoute requiredRole="ta" loginPath="/login/ta"><TaReview /></ProtectedRoute>} />

        {/* 404 fallback */}
        <Route path="*" element={
          <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <p className="text-6xl font-bold text-gray-200">404</p>
              <p className="text-gray-500 mt-2">Page not found.</p>
            </div>
          </div>
        } />
      </Routes>
    </>
  );
}
