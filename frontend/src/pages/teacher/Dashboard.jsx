// teacher/Dashboard.jsx — lists all exam papers created by the teacher.

import { Link } from "react-router-dom";
import { useTeacherPapers } from "../../hooks/usePapers";
import PageWrapper from "../../components/layout/PageWrapper";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import { SkeletonCard } from "../../components/ui/Skeleton";
import { formatDate, paperTypeLabel } from "../../utils/formatters";

// Badge colour per paper type
const TYPE_VARIANT = {
  mcq: "indigo",
  mcq_numerical: "info",
  mcq_numerical_subjective: "warning",
};

// One paper as a register row: name + subject, type, marks / questions / results, links
function PaperRow({ paper }) {
  const totalQuestions = (paper.mcqCount ?? 0) + (paper.numericalCount ?? 0) + (paper.subjectiveCount ?? 0);
  return (
    <li className="grid grid-cols-[minmax(0,1fr)_auto] md:grid-cols-[minmax(0,1fr)_auto_repeat(3,5rem)_auto] items-center gap-x-6 gap-y-2 py-4">
      <div className="min-w-0">
        <p className="text-gray-900 font-medium">{paper.name}</p>
        <p className="text-xs text-gray-500">{paper.subject} · created {formatDate(paper.createdAt)}</p>
      </div>
      <div className="hidden md:block"><Badge variant={TYPE_VARIANT[paper.type] ?? "neutral"}>{paperTypeLabel(paper.type)}</Badge></div>
      {[["Marks", paper.totalMarks], ["Questions", totalQuestions], ["Results", paper.resultCount]].map(([label, v]) => (
        <div key={label} className="hidden md:block">
          <p className="kicker">{label}</p>
          <p className="font-mono text-gray-900">{v}</p>
        </div>
      ))}
      <div className="flex gap-2 justify-end">
        <Link to={`/teacher/papers/${paper.id}/results`}><Button size="sm">View Results</Button></Link>
        <Link to={`/teacher/papers/${paper.id}/view`}><Button variant="secondary" size="sm">View Paper</Button></Link>
      </div>
    </li>
  );
}

export default function TeacherDashboard() {
  const { papers, loading } = useTeacherPapers();

  return (
    <PageWrapper>
      {/* Header + create button */}
      <div className="flex items-end justify-between mb-6">
        <div>
          <p className="kicker">Teacher</p>
          <h1 className="text-3xl text-gray-900">My papers</h1>
          <p className="text-sm text-gray-500 mt-1">Create exam papers and follow every student's result.</p>
        </div>
        <Link to="/teacher/papers/create"><Button>Create paper</Button></Link>
      </div>

      {/* Paper register (placeholders while loading) */}
      {loading ? (
        <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}</div>
      ) : papers.length === 0 ? (
        <p className="py-16 text-gray-500 border-y border-gray-300">No papers yet. Use "Create paper" to add your first exam.</p>
      ) : (
        <ul className="border-y border-gray-900 divide-y divide-gray-300">
          {papers.map((p) => <PaperRow key={p.id} paper={p} />)}
        </ul>
      )}
    </PageWrapper>
  );
}
