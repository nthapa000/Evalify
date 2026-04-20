// teacher/PaperResults.jsx — shows all student submissions for one paper.
// Displays a stat bar (avg/highest/lowest) and a per-student results table.

import { useParams, Link } from "react-router-dom";
import { usePaperResults } from "../../hooks/usePapers";
import PageWrapper from "../../components/layout/PageWrapper";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import { SkeletonRow } from "../../components/ui/Skeleton";
import { formatDateTime, formatPercent, gradeFromPercent } from "../../utils/formatters";

// Map percentage to a badge color
const gradeBadgeVariant = (pct) => {
  if (pct >= 80) return "success";
  if (pct >= 50) return "info";
  return "error";
};

export default function PaperResults() {
  const { paperId } = useParams();
  const { data, loading } = usePaperResults(paperId);

  return (
    <PageWrapper>
      {/* Back link */}
      <Link to="/teacher/dashboard" className="text-sm text-indigo-600 hover:underline mb-4 inline-block">
        ← Back to Dashboard
      </Link>

      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        {loading ? "Loading…" : `Results — ${data?.submissions?.[0]?.paper_name ?? "Paper"}`}
      </h1>

      {/* Stats bar */}
      {!loading && data && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[
            { label: "Submissions", value: data.stats.count },
            { label: "Average Score", value: data.stats.average },
            { label: "Highest Score", value: data.stats.highest },
            { label: "Lowest Score", value: data.stats.lowest },
          ].map((s) => (
            <Card key={s.label} className="text-center">
              <Card.Body>
                <p className="text-2xl font-bold text-indigo-600">{s.value}</p>
                <p className="text-xs text-gray-500 mt-1">{s.label}</p>
              </Card.Body>
            </Card>
          ))}
        </div>
      )}

      {/* Results table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-left">
                {["Student Name", "Roll No", "Score", "Percentage", "Grade", "Submitted"].map((h) => (
                  <th key={h} className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading
                ? Array.from({ length: 3 }).map((_, i) => <SkeletonRow key={i} />)
                : data?.submissions?.length === 0
                ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-10 text-center text-gray-400">
                      No submissions yet.
                    </td>
                  </tr>
                )
                : data?.submissions?.map((sub) => (
                  <tr key={sub.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-800">{sub.student_name}</td>
                    <td className="px-6 py-4 text-gray-600">{sub.roll_no}</td>
                    <td className="px-6 py-4 text-gray-800">
                      {sub.result.totalScore} / {sub.result.maxScore}
                    </td>
                    <td className="px-6 py-4">{formatPercent(sub.result.percentage)}</td>
                    <td className="px-6 py-4">
                      <Badge variant={gradeBadgeVariant(sub.result.percentage)}>
                        {gradeFromPercent(sub.result.percentage)}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-gray-400 text-xs">{formatDateTime(sub.submittedAt)}</td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        </div>
      </Card>
    </PageWrapper>
  );
}
