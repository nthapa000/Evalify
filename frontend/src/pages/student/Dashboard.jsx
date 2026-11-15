// student/Dashboard.jsx — shows subject cards for the logged-in student.

import { Link } from "react-router-dom";
import useAuthStore from "../../store/authStore";
import { useAvailablePapers } from "../../hooks/useSubmission";
import PageWrapper from "../../components/layout/PageWrapper";
import StatLedger from "../../components/ui/StatLedger";
import { SkeletonCard } from "../../components/ui/Skeleton";

export default function StudentDashboard() {
  const { user } = useAuthStore();
  const { papers, loading } = useAvailablePapers();

  // Count papers per subject → one card per subject that has papers
  const paperCountBySubject = papers.reduce((acc, p) => {
    if (p.subject) acc[p.subject] = (acc[p.subject] ?? 0) + 1;
    return acc;
  }, {});

  const activeSubjects = Object.keys(paperCountBySubject).map((name) => ({ name }));

  const count = (status) => papers.filter((p) => p.submissionStatus === status).length;
  const pendingCount = count("not_submitted");

  return (
    <PageWrapper>
      {/* Greeting + pending count */}
      <div className="mb-6">
        <p className="kicker">Student</p>
        <h1 className="text-3xl text-gray-900">Welcome, {user?.name}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {loading ? "Loading your papers…" : `${pendingCount} exam${pendingCount !== 1 ? "s" : ""} pending submission`}
        </p>
      </div>

      {/* Totals: all / pending / evaluated */}
      {!loading && papers.length > 0 && (
        <div className="mb-8">
          <StatLedger items={[
            { label: "Papers", value: papers.length },
            { label: "Pending", value: pendingCount },
            { label: "Evaluated", value: count("evaluated") },
          ]} />
        </div>
      )}

      {/* Subjects as an index (placeholders while loading) */}
      <p className="kicker mb-2">Subjects</p>
      {loading ? (
        <SkeletonCard />
      ) : activeSubjects.length === 0 ? (
        <p className="py-10 text-gray-500 border-y border-gray-300">No exam papers available yet.</p>
      ) : (
        <ul className="border-y border-gray-900 divide-y divide-gray-300">
          {activeSubjects.map((sub, i) => {
            const n = paperCountBySubject[sub.name] ?? 0;
            return (
              <li key={sub.name}>
                <Link to={`/student/subjects/${encodeURIComponent(sub.name)}`}
                      className="flex items-baseline gap-4 py-3 group">
                  <span className="font-mono text-xs text-gray-400">{String(i + 1).padStart(2, "0")}</span>
                  <span className="flex-1 text-gray-900 group-hover:text-green-700 group-hover:underline underline-offset-4">{sub.name}</span>
                  <span className="font-mono text-xs text-gray-500">{n} paper{n !== 1 ? "s" : ""}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </PageWrapper>
  );
}
