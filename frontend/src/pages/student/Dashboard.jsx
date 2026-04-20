// student/Dashboard.jsx — shows subject cards for the logged-in student.
// Clicking a card navigates to that subject's available papers.

import { Link } from "react-router-dom";
import useAuthStore from "../../store/authStore";
import { useAvailablePapers } from "../../hooks/useSubmission";
import PageWrapper from "../../components/layout/PageWrapper";
import Card from "../../components/ui/Card";
import { SkeletonCard } from "../../components/ui/Skeleton";

// Icon/color lookup for known subjects; unknown subjects get a default
const SUBJECT_META = {
  "Computer Science": { icon: "💻", color: "bg-indigo-100 text-indigo-700" },
  "Mathematics":      { icon: "📐", color: "bg-blue-100 text-blue-700" },
  "Physics":          { icon: "⚛️",  color: "bg-purple-100 text-purple-700" },
  "Chemistry":        { icon: "🧪", color: "bg-green-100 text-green-700" },
  "Biology":          { icon: "🧬", color: "bg-emerald-100 text-emerald-700" },
  "English":          { icon: "📚", color: "bg-yellow-100 text-yellow-700" },
  "History":          { icon: "🏛️",  color: "bg-orange-100 text-orange-700" },
};

export default function StudentDashboard() {
  const { user } = useAuthStore();
  const { papers, loading } = useAvailablePapers();

  // Count papers per subject and derive unique subject list from actual papers
  const paperCountBySubject = papers.reduce((acc, p) => {
    if (p.subject) acc[p.subject] = (acc[p.subject] ?? 0) + 1;
    return acc;
  }, {});

  const DEFAULT_META = { icon: "📖", color: "bg-gray-100 text-gray-700" };
  const activeSubjects = Object.keys(paperCountBySubject).map((name) => ({
    name,
    ...( SUBJECT_META[name] ?? DEFAULT_META ),
  }));

  const pendingCount = papers.filter((p) => p.submissionStatus === "not_submitted").length;

  return (
    <PageWrapper>
      {/* Welcome header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Welcome, {user?.name}! 👋</h1>
        <p className="text-sm text-gray-500 mt-1">
          {loading ? "Loading your papers…" : `${pendingCount} exam${pendingCount !== 1 ? "s" : ""} pending submission`}
        </p>
      </div>

      {/* Subject cards */}
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Subjects</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
          : activeSubjects.length === 0
            ? (
              <div className="col-span-4 text-center py-16 text-gray-400">
                <p className="text-4xl mb-2">📭</p>
                <p className="text-sm">No exam papers available yet.</p>
              </div>
            )
            : activeSubjects.map((sub) => {
              const count = paperCountBySubject[sub.name] ?? 0;
              return (
                <Link key={sub.name} to={`/student/subjects/${encodeURIComponent(sub.name)}`}>
                  <Card className="hover:shadow-md transition-shadow cursor-pointer group">
                    <Card.Body className="flex flex-col items-center text-center py-8 gap-3">
                      <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-3xl ${sub.color}`}>
                        {sub.icon}
                      </div>
                      <p className="font-semibold text-gray-800 group-hover:text-indigo-600 transition-colors">
                        {sub.name}
                      </p>
                      <p className="text-xs text-gray-400">
                        {count > 0 ? `${count} paper${count > 1 ? "s" : ""} available` : "No papers yet"}
                      </p>
                    </Card.Body>
                  </Card>
                </Link>
              );
            })
        }
      </div>

      {/* Quick stats */}
      {!loading && papers.length > 0 && (
        <div className="mt-8">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Overview</h2>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: "Total Papers", value: papers.length },
              { label: "Pending",      value: papers.filter((p) => p.submissionStatus === "not_submitted").length },
              { label: "Evaluated",    value: papers.filter((p) => p.submissionStatus === "evaluated").length },
            ].map((s) => (
              <Card key={s.label} className="text-center">
                <Card.Body>
                  <p className="text-2xl font-bold text-indigo-600">{s.value}</p>
                  <p className="text-xs text-gray-500 mt-1">{s.label}</p>
                </Card.Body>
              </Card>
            ))}
          </div>
        </div>
      )}
    </PageWrapper>
  );
}
