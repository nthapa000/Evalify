// student/Result.jsx — shows the evaluation result for a completed submission.

import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useResult } from "../../hooks/useSubmission";
import useAuthStore from "../../store/authStore";
import PageWrapper from "../../components/layout/PageWrapper";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";
import { formatPercent, gradeFromPercent } from "../../utils/formatters";

function ScoreCircle({ score, max }) {
  const pct   = max > 0 ? (score / max) * 100 : 0;
  const grade = gradeFromPercent(pct);
  const color = pct >= 80 ? "text-green-600" : pct >= 50 ? "text-green-500" : "text-red-500";

  return (
    <div className="flex flex-col items-center">
      <div className="w-32 h-32 rounded-full border-8 border-green-100 flex flex-col items-center justify-center">
        <span className={`text-3xl font-bold ${color}`}>{score}</span>
        <span className="text-xs text-gray-400">/ {max}</span>
      </div>
      <Badge
        variant={pct >= 80 ? "success" : pct >= 50 ? "info" : "error"}
        className="mt-3 text-sm px-4 py-1"
      >
        Grade {grade}
      </Badge>
    </div>
  );
}

export default function Result() {
  const { submissionId } = useParams();
  const { data, loading } = useResult(submissionId);
  const token = useAuthStore((s) => s.token);
  const [fileLoading, setFileLoading] = useState(false);

  const viewAnswerSheet = async () => {
    setFileLoading(true);
    try {
      const res = await fetch(`/api/submissions/${submissionId}/file`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load file");
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      window.open(url, "_blank");
    } catch {
      alert("Could not load answer sheet.");
    } finally {
      setFileLoading(false);
    }
  };

  if (loading) {
    return (
      <PageWrapper>
        <div className="max-w-2xl mx-auto space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      </PageWrapper>
    );
  }

  if (!data) {
    return (
      <PageWrapper>
        <div className="text-center py-20 text-gray-400">
          <p className="text-lg font-medium">Result not available yet.</p>
          <Link to="/student/dashboard" className="text-sm text-green-600 hover:underline mt-2 inline-block">
            &larr; Back to Dashboard
          </Link>
        </div>
      </PageWrapper>
    );
  }

  const { result, student_name, roll_no, paper_name, stats, paper } = data;
  const isType2 = paper?.type === "mcq_numerical" || paper?.type === "mcq_numerical_subjective";
  const isType3 = paper?.type === "mcq_numerical_subjective";

  return (
    <PageWrapper>
      <Link to="/student/dashboard" className="text-sm text-green-600 hover:underline mb-4 inline-block">
        &larr; Back to Dashboard
      </Link>

      <h1 className="text-2xl font-bold text-gray-800 mb-6">{paper_name} — Result</h1>

      <Card className="mb-6">
        <Card.Body>
          <div className="flex flex-col md:flex-row items-center gap-8">
            <ScoreCircle score={result.totalScore} max={result.maxScore} />

            <div className="flex-1 space-y-3 text-center md:text-left">
              <div>
                <p className="text-xl font-bold text-gray-800">{student_name}</p>
                <p className="text-sm text-gray-500">Roll No: {roll_no}</p>
              </div>

              <div className="grid grid-cols-3 gap-3 mt-4">
                <div className="bg-green-50 rounded-xl p-3 text-center">
                  <p className="text-lg font-bold text-green-600">{result.totalScore}/{result.maxScore}</p>
                  <p className="text-xs text-gray-500">Your Score</p>
                </div>
                <div className="bg-gray-50 rounded-xl p-3 text-center">
                  <p className="text-lg font-bold text-gray-700">{stats.average}/{result.maxScore}</p>
                  <p className="text-xs text-gray-500">Class Average</p>
                </div>
                <div className="bg-green-50 rounded-xl p-3 text-center">
                  <p className="text-lg font-bold text-green-600">{stats.highest}/{result.maxScore}</p>
                  <p className="text-xs text-gray-500">Highest</p>
                </div>
              </div>

              <p className="text-sm text-gray-500">
                Percentage: <strong>{formatPercent(result.percentage)}</strong>
              </p>
            </div>
          </div>
        </Card.Body>
      </Card>

      <div className="mb-4">
        <button
          type="button"
          onClick={viewAnswerSheet}
          disabled={fileLoading}
          className="inline-flex items-center gap-2 text-sm text-green-600 hover:text-green-800 border border-green-200 hover:border-green-400 rounded-lg px-4 py-2 bg-green-50 hover:bg-green-100 transition-colors disabled:opacity-50"
        >
          {fileLoading ? "Loading…" : "View My Answer Sheet"}
        </button>
      </div>

      <Card>
        <Card.Header>
          <h2 className="text-base font-semibold text-gray-700">Section Breakdown</h2>
        </Card.Header>
        <Card.Body className="space-y-3">
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">MCQ Section</span>
            <span className="font-semibold text-gray-800">{result.mcqScore} / {(paper?.mcqCount ?? 0) * (paper?.mcqMarks ?? 0) || "—"}</span>
          </div>
          {isType2 && (
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Numerical Section</span>
              <span className="font-semibold text-gray-800">{result.numericalScore} / {(paper?.numericalCount ?? 0) * (paper?.numericalMarks ?? 0) || "—"}</span>
            </div>
          )}
          {isType3 && (
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Subjective Section</span>
              <span className="font-semibold text-gray-800">{result.subjectiveScore} / {(paper?.subjectiveCount ?? 0) * (paper?.subjectiveMarks ?? 0) || "—"}</span>
            </div>
          )}
          <div className="flex justify-between items-center py-2 font-bold">
            <span className="text-gray-800">Total</span>
            <span className="text-green-600">{result.totalScore} / {result.maxScore}</span>
          </div>
        </Card.Body>
      </Card>
    </PageWrapper>
  );
}
