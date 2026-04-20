// student/SubjectPage.jsx — lists all exam papers for one subject.
// Shows submission status (not submitted / processing / evaluated) for each paper.

import { useParams, Link } from "react-router-dom";
import { useAvailablePapers } from "../../hooks/useSubmission";
import PageWrapper from "../../components/layout/PageWrapper";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import { SkeletonCard } from "../../components/ui/Skeleton";
import { formatDate, paperTypeLabel, statusLabel } from "../../utils/formatters";

const STATUS_VARIANT = {
  not_submitted: "neutral",
  processing:    "warning",
  evaluated:     "success",
};

export default function SubjectPage() {
  const { subject } = useParams();
  const decodedSubject = decodeURIComponent(subject);
  const { papers, loading } = useAvailablePapers();

  // Filter to the current subject only
  const subjectPapers = papers.filter((p) => p.subject === decodedSubject);

  return (
    <PageWrapper>
      <Link to="/student/dashboard" className="text-sm text-indigo-600 hover:underline mb-4 inline-block">
        ← Back to Dashboard
      </Link>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">{decodedSubject}</h1>
        <span className="text-sm text-gray-500">{subjectPapers.length} paper(s)</span>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 2 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : subjectPapers.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <p className="text-5xl mb-3">📭</p>
          <p className="text-lg font-medium">No papers available for {decodedSubject}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {subjectPapers.map((paper) => (
            <Card key={paper.id} className="hover:shadow-md transition-shadow">
              <Card.Body>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-semibold text-gray-800">{paper.name}</h3>
                    <p className="text-xs text-gray-500 mt-0.5">{paperTypeLabel(paper.type)}</p>
                  </div>
                  <Badge variant={STATUS_VARIANT[paper.submissionStatus]}>
                    {statusLabel(paper.submissionStatus)}
                  </Badge>
                </div>

                <div className="mt-3 flex gap-4 text-sm text-gray-500">
                  <span>📊 {paper.totalMarks} marks</span>
                  <span>📅 {formatDate(paper.createdAt)}</span>
                </div>
              </Card.Body>
              <Card.Footer className="flex gap-2">
                {paper.submissionStatus === "not_submitted" && (
                  <Link to={`/student/submit/${paper.id}`} className="flex-1">
                    <Button size="sm" className="w-full">Upload Answer Sheet</Button>
                  </Link>
                )}
                {paper.submissionStatus === "processing" && (
                  <Button size="sm" variant="secondary" disabled className="flex-1">
                    ⏳ Evaluating…
                  </Button>
                )}
                {paper.submissionStatus === "evaluated" && (
                  <Link to={`/student/results/${paper.submissionId}`} className="flex-1">
                    <Button size="sm" variant="secondary" className="w-full">View Result</Button>
                  </Link>
                )}
              </Card.Footer>
            </Card>
          ))}
        </div>
      )}
    </PageWrapper>
  );
}
