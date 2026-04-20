// student/Submission.jsx — student uploads their answer sheet for evaluation.
// After submission, polls every 2s for evaluation status, then redirects to Result.

import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useSubmitAnswerSheet, useSubmissionStatus } from "../../hooks/useSubmission";
import PageWrapper from "../../components/layout/PageWrapper";
import UploadZone from "../../components/forms/UploadZone";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";

export default function Submission() {
  const { paperId } = useParams();
  const navigate = useNavigate();
  const { submit, loading } = useSubmitAnswerSheet();

  const [file, setFile]               = useState(null);
  const [submissionId, setSubmissionId] = useState(null);

  // Once we have a submissionId, poll for status
  const { status } = useSubmissionStatus(submissionId);

  // Redirect to result page as soon as evaluation completes
  useEffect(() => {
    if (status === "evaluated" && submissionId) {
      navigate(`/student/results/${submissionId}`);
    }
  }, [status, submissionId, navigate]);

  const handleSubmit = async () => {
    if (!file) return;
    const sub = await submit(paperId);
    if (sub) setSubmissionId(sub.id);
  };

  // Waiting for evaluation state
  if (submissionId) {
    return (
      <PageWrapper>
        <div className="max-w-md mx-auto mt-20 text-center">
          <div className="text-6xl mb-4 animate-bounce">⏳</div>
          <h2 className="text-xl font-bold text-gray-800">Evaluating Your Answer Sheet</h2>
          <p className="text-gray-500 text-sm mt-2">
            Our AI is grading your paper. This usually takes a few seconds.
          </p>
          {/* Progress dots animation */}
          <div className="flex justify-center gap-1.5 mt-6">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-2.5 h-2.5 bg-indigo-400 rounded-full animate-pulse"
                style={{ animationDelay: `${i * 0.2}s` }}
              />
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-4">Status: {status}</p>
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper>
      <Link to="/student/dashboard" className="text-sm text-indigo-600 hover:underline mb-4 inline-block">
        ← Back to Dashboard
      </Link>

      <div className="max-w-lg mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Upload Answer Sheet</h1>
        <p className="text-sm text-gray-500 mb-6">
          Upload a clear, well-lit scan or photo of your handwritten answer sheet.
        </p>

        <Card>
          <Card.Body className="space-y-5">
            <UploadZone
              onFileSelect={setFile}
              label="Upload your answer sheet"
              hint="JPG, PNG, or PDF. Max 10 MB. Ensure text is legible."
            />

            {/* Tips for a good scan */}
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-700 space-y-1">
              <p className="font-semibold">📸 Tips for best results:</p>
              <p>• Place the sheet on a flat, well-lit surface</p>
              <p>• Capture the full sheet without cropping</p>
              <p>• Avoid shadows and glare</p>
            </div>
          </Card.Body>
          <Card.Footer className="flex gap-3">
            <Link to="/student/dashboard">
              <Button variant="secondary">Cancel</Button>
            </Link>
            <Button
              onClick={handleSubmit}
              loading={loading}
              disabled={!file}
              className="flex-1"
            >
              Submit for Evaluation
            </Button>
          </Card.Footer>
        </Card>
      </div>
    </PageWrapper>
  );
}
