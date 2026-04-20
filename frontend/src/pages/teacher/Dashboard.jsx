// teacher/Dashboard.jsx — lists all exam papers created by the teacher.
// Shows skeleton cards while loading; each card links to results view.

import { Link } from "react-router-dom";
import { useTeacherPapers } from "../../hooks/usePapers";
import PageWrapper from "../../components/layout/PageWrapper";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import { SkeletonCard } from "../../components/ui/Skeleton";
import { formatDate, paperTypeLabel } from "../../utils/formatters";

// Badge variant per paper type
const TYPE_VARIANT = {
  mcq: "indigo",
  mcq_numerical: "info",
  mcq_numerical_subjective: "warning",
};

function PaperCard({ paper }) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <Card.Body>
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-gray-800 truncate">{paper.name}</h3>
            <p className="text-sm text-gray-500 mt-0.5">{paper.subject}</p>
          </div>
          <Badge variant={TYPE_VARIANT[paper.type] ?? "neutral"}>
            {paperTypeLabel(paper.type)}
          </Badge>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-3 text-center">
          <div className="bg-gray-50 rounded-lg py-2">
            <p className="text-lg font-bold text-gray-800">{paper.totalMarks}</p>
            <p className="text-xs text-gray-400">Total Marks</p>
          </div>
          <div className="bg-gray-50 rounded-lg py-2">
            <p className="text-lg font-bold text-gray-800">{paper.mcqCount}</p>
            <p className="text-xs text-gray-400">Questions</p>
          </div>
          <div className="bg-gray-50 rounded-lg py-2">
            <p className="text-lg font-bold text-indigo-600">{paper.resultCount}</p>
            <p className="text-xs text-gray-400">Results</p>
          </div>
        </div>

        <p className="text-xs text-gray-400 mt-3">Created {formatDate(paper.createdAt)}</p>
      </Card.Body>
      <Card.Footer className="flex gap-2">
        <Link to={`/teacher/papers/${paper.id}/results`} className="flex-1">
          <Button variant="primary" size="sm" className="w-full">View Results</Button>
        </Link>
        <Link to={`/teacher/papers/${paper.id}/view`}>
          <Button variant="secondary" size="sm">View Paper</Button>
        </Link>
      </Card.Footer>
    </Card>
  );
}

export default function TeacherDashboard() {
  const { papers, loading } = useTeacherPapers();

  return (
    <PageWrapper>
      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">My Papers</h1>
          <p className="text-sm text-gray-500 mt-1">Manage your exam papers and view student results</p>
        </div>
        <Link to="/teacher/papers/create">
          <Button>+ Create Paper</Button>
        </Link>
      </div>

      {/* Paper grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {loading
          ? Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)
          : papers.length === 0
            ? (
              // Empty state
              <div className="col-span-3 text-center py-20 text-gray-400">
                <p className="text-5xl mb-3">📋</p>
                <p className="text-lg font-medium">No papers yet</p>
                <p className="text-sm mt-1">Click "Create Paper" to add your first exam.</p>
              </div>
            )
            : papers.map((p) => <PaperCard key={p.id} paper={p} />)
        }
      </div>
    </PageWrapper>
  );
}
