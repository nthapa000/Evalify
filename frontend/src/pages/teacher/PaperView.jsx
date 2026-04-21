// teacher/PaperView.jsx — read-only view of a paper's details, answer key, and uploaded PDFs.
// Teachers can see question paper PDF + answer key reference PDF from this page.

import { useParams, Link } from "react-router-dom";
import { usePaperView } from "../../hooks/usePapers";
import PageWrapper from "../../components/layout/PageWrapper";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import { SkeletonCard } from "../../components/ui/Skeleton";
import { paperTypeLabel } from "../../utils/formatters";

const TYPE_VARIANT = {
    mcq: "indigo",
    mcq_numerical: "info",
    mcq_numerical_subjective: "warning",
};

const MCQ_OPTIONS = ["A", "B", "C", "D"];

export default function PaperView() {
    const { paperId } = useParams();
    const { paper, loading } = usePaperView(paperId);

    if (loading) {
        return (
            <PageWrapper>
                <div className="max-w-3xl mx-auto space-y-4">
                    <SkeletonCard />
                    <SkeletonCard />
                </div>
            </PageWrapper>
        );
    }

    if (!paper) {
        return (
            <PageWrapper>
                <div className="text-center py-20 text-gray-400">
                    <p className="text-5xl mb-3">📄</p>
                    <p className="text-lg font-medium">Paper not found</p>
                </div>
            </PageWrapper>
        );
    }

    const isType2 = paper.type === "mcq_numerical" || paper.type === "mcq_numerical_subjective";
    const isType3 = paper.type === "mcq_numerical_subjective";

    return (
        <PageWrapper>
            <Link to="/teacher/dashboard" className="text-sm text-green-600 hover:underline mb-4 inline-block">
                ← Back to Dashboard
            </Link>

            {/* Paper Header */}
            <div className="max-w-3xl mx-auto space-y-6">
                <div className="flex items-start justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800">{paper.name}</h1>
                        <p className="text-sm text-gray-500 mt-1">{paper.subject}</p>
                    </div>
                    <Badge variant={TYPE_VARIANT[paper.type] ?? "neutral"}>
                        {paperTypeLabel(paper.type)}
                    </Badge>
                </div>

                {/* Marks Overview */}
                <Card>
                    <Card.Header>
                        <h2 className="text-base font-semibold text-gray-700">📊 Marks Overview</h2>
                    </Card.Header>
                    <Card.Body>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                            <div className="bg-green-50 rounded-lg py-3">
                                <p className="text-2xl font-bold text-green-600">{paper.totalMarks}</p>
                                <p className="text-xs text-gray-500 mt-1">Total Marks</p>
                            </div>
                            <div className="bg-gray-50 rounded-lg py-3">
                                <p className="text-2xl font-bold text-gray-800">{paper.mcqCount}</p>
                                <p className="text-xs text-gray-500 mt-1">MCQ Questions</p>
                            </div>
                            {isType2 && (
                                <div className="bg-gray-50 rounded-lg py-3">
                                    <p className="text-2xl font-bold text-gray-800">{paper.numericalCount}</p>
                                    <p className="text-xs text-gray-500 mt-1">Numerical Qs</p>
                                </div>
                            )}
                            {isType3 && (
                                <div className="bg-gray-50 rounded-lg py-3">
                                    <p className="text-2xl font-bold text-gray-800">{paper.subjectiveCount}</p>
                                    <p className="text-xs text-gray-500 mt-1">Subjective Qs</p>
                                </div>
                            )}
                        </div>
                        {paper.config?.negativeMaking && (
                            <p className="text-xs text-red-500 mt-3 text-center">
                                ⚠ Negative marking: −{paper.config.marksDeducted ?? 0.5} per wrong answer
                                {paper.config.negativeMarkingScope === "per_question" && paper.config.negativeMarkingQuestions?.length > 0
                                    ? ` — applies to ${paper.config.negativeMarkingQuestions.join(", ")}`
                                    : " — all questions"
                                }
                            </p>
                        )}
                    </Card.Body>
                </Card>

                {/* Uploaded Documents */}
                {(paper.questionPaperUrl || paper.answerKeyRefUrl || paper.answerSheetRefUrl) && (
                    <Card>
                        <Card.Header>
                            <h2 className="text-base font-semibold text-gray-700">📎 Uploaded Documents</h2>
                        </Card.Header>
                        <Card.Body className="space-y-3">
                            {paper.questionPaperUrl && (
                                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-200">
                                    <div className="flex items-center gap-3">
                                        <span className="text-2xl">📄</span>
                                        <div>
                                            <p className="text-sm font-medium text-gray-700">Question Paper (Reference)</p>
                                            <p className="text-xs text-gray-400">PDF reference for this exam paper</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => window.open(paper.questionPaperUrl, "_blank")}
                                        className="text-sm text-green-600 hover:underline font-medium"
                                    >
                                        View PDF ↗
                                    </button>
                                </div>
                            )}
                            {paper.answerKeyRefUrl && (
                                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-200">
                                    <div className="flex items-center gap-3">
                                        <span className="text-2xl">📝</span>
                                        <div>
                                            <p className="text-sm font-medium text-gray-700">Answer Key (Reference)</p>
                                            <p className="text-xs text-gray-400">Uploaded answer key PDF for reference</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => window.open(paper.answerKeyRefUrl, "_blank")}
                                        className="text-sm text-green-600 hover:underline font-medium"
                                    >
                                        View PDF ↗
                                    </button>
                                </div>
                            )}
                            {paper.answerSheetRefUrl && (
                                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-200">
                                    <div className="flex items-center gap-3">
                                        <span className="text-2xl">📋</span>
                                        <div>
                                            <p className="text-sm font-medium text-gray-700">Answer Sheet (Reference)</p>
                                            <p className="text-xs text-gray-400">Teacher's completed answer sheet for reference</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => window.open(paper.answerSheetRefUrl, "_blank")}
                                        className="text-sm text-green-600 hover:underline font-medium"
                                    >
                                        View PDF ↗
                                    </button>
                                </div>
                            )}
                        </Card.Body>
                    </Card>
                )}

                {/* MCQ Answer Key */}
                {paper.mcqAnswers && Object.keys(paper.mcqAnswers).length > 0 && (
                    <Card>
                        <Card.Header>
                            <h2 className="text-base font-semibold text-gray-700">☑️ MCQ Answer Key</h2>
                        </Card.Header>
                        <Card.Body>
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                                {Array.from({ length: paper.mcqCount }, (_, i) => {
                                    const qid = `Q${i + 1}`;
                                    const answer = paper.mcqAnswers[qid];
                                    const marks = paper.mcqQuestionMarks?.[qid] ?? paper.mcqMarks;
                                    return (
                                        <div key={qid} className="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2">
                                            <span className="text-xs font-medium text-gray-500 w-8">{qid}</span>
                                            <span className="text-xs text-gray-400 w-8">[{marks}m]</span>
                                            <div className="flex gap-1">
                                                {MCQ_OPTIONS.map((opt) => (
                                                    <span
                                                        key={opt}
                                                        className={`w-7 h-7 rounded-lg text-xs font-semibold flex items-center justify-center
                              ${answer === opt
                                                                ? "bg-green-600 text-white"
                                                                : "bg-white border border-gray-200 text-gray-300"}`}
                                                    >
                                                        {opt}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </Card.Body>
                    </Card>
                )}

                {/* Numerical Answers */}
                {isType2 && paper.numericalAnswers && Object.keys(paper.numericalAnswers).length > 0 && (
                    <Card>
                        <Card.Header>
                            <h2 className="text-base font-semibold text-gray-700">🔢 Numerical Answers</h2>
                        </Card.Header>
                        <Card.Body>
                            <div className="space-y-2">
                                {Array.from({ length: paper.numericalCount }, (_, i) => {
                                    const qid = `N${i + 1}`;
                                    const ans = paper.numericalAnswers[qid];
                                    const marks = paper.numericalQuestionMarks?.[qid] ?? paper.numericalMarks;
                                    if (!ans) return null;
                                    return (
                                        <div key={qid} className="flex items-center gap-3 bg-gray-50 rounded-lg px-3 py-2">
                                            <span className="text-xs font-medium text-gray-500 w-6">{qid}</span>
                                            <span className="text-xs text-gray-400">[{marks}m]</span>
                                            <span className="text-sm font-mono text-gray-800">{ans.answer}</span>
                                            <span className="text-xs text-gray-400">
                                                ({ans.tolerance_type === "exact" ? "Exact" :
                                                    ans.tolerance_type === "range" ? `±${ans.tolerance_value}` :
                                                        "Variants"})
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        </Card.Body>
                    </Card>
                )}

                {/* Subjective Questions */}
                {isType3 && paper.subjectiveQuestions && paper.subjectiveQuestions.length > 0 && (
                    <Card>
                        <Card.Header>
                            <h2 className="text-base font-semibold text-gray-700">✍️ Subjective Questions</h2>
                        </Card.Header>
                        <Card.Body className="space-y-4">
                            {paper.subjectiveQuestions.map((sq, i) => {
                                const marks = paper.subjectiveQuestionMarks?.[`S${i + 1}`] ?? paper.subjectiveMarks ?? sq.max_marks;
                                return (
                                    <div key={i} className="bg-gray-50 rounded-xl p-4 space-y-2">
                                        <div className="flex items-center justify-between">
                                            <span className="text-xs font-semibold text-gray-500">S{i + 1}</span>
                                            <span className="text-xs text-gray-400">[{marks} marks]</span>
                                        </div>
                                        <p className="text-sm text-gray-700">{sq.question_text}</p>
                                        {sq.rubric && (
                                            <div className="text-xs text-gray-400 space-y-1">
                                                <p><strong>Key Concepts:</strong> {sq.rubric.key_concepts?.join(", ")}</p>
                                                {sq.rubric.mandatory_concepts?.length > 0 && (
                                                    <p><strong>Mandatory:</strong> {sq.rubric.mandatory_concepts.join(", ")}</p>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </Card.Body>
                    </Card>
                )}

                {/* Action buttons */}
                <div className="flex gap-3">
                    <Link to={`/teacher/papers/${paperId}/results`} className="flex-1">
                        <Button variant="primary" className="w-full">View Results</Button>
                    </Link>
                    <Link to="/teacher/dashboard">
                        <Button variant="secondary">Back to Dashboard</Button>
                    </Link>
                </div>
            </div>
        </PageWrapper>
    );
}
