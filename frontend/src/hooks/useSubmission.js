// useSubmission.js — student-side data hook for submitting and checking results.
// Phase 2: replace mock functions with api.post("/submissions") calls.

import { useState, useEffect, useRef } from "react";
import { mockGetAvailablePapers, mockSubmitAnswerSheet, mockGetSubmissionStatus, mockGetResult } from "../utils/mockData";
import useToastStore from "../store/toastStore";
import useAuthStore from "../store/authStore";

// List all papers available to the student with their submission status
export function useAvailablePapers() {
  const { user } = useAuthStore();
  const [papers, setPapers]   = useState([]);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToastStore();

  useEffect(() => {
    if (!user?.id) return;
    setLoading(true);
    mockGetAvailablePapers(user.id)
      .then(setPapers)
      .catch(() => addToast("Failed to load papers.", "error"))
      .finally(() => setLoading(false));
  }, [user?.id]);

  return { papers, loading };
}

// Handle submission of an answer sheet image
export function useSubmitAnswerSheet() {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const { addToast } = useToastStore();

  const submit = async (paperId) => {
    setLoading(true);
    try {
      // Phase 3+: pass the actual File object; here we only simulate
      const sub = await mockSubmitAnswerSheet(paperId, user.id, user.name, user.roll_no);
      addToast("Answer sheet submitted! Evaluating…", "info");
      return sub;
    } catch (e) {
      addToast("Submission failed. Try again.", "error");
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { submit, loading };
}

// Poll submission status every 2s until it reaches "evaluated"
export function useSubmissionStatus(submissionId) {
  const [status, setStatus]   = useState("processing");
  const [result, setResult]   = useState(null);
  const intervalRef = useRef();

  useEffect(() => {
    if (!submissionId) return;
    const poll = async () => {
      try {
        const { status: s, result: r } = await mockGetSubmissionStatus(submissionId);
        setStatus(s);
        if (s === "evaluated") {
          setResult(r);
          clearInterval(intervalRef.current); // stop polling once done
        }
      } catch {
        clearInterval(intervalRef.current);
      }
    };
    poll();
    intervalRef.current = setInterval(poll, 2000);
    return () => clearInterval(intervalRef.current);
  }, [submissionId]);

  return { status, result };
}

// Fetch the full result object for a completed submission
export function useResult(submissionId) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToastStore();

  useEffect(() => {
    if (!submissionId) return;
    mockGetResult(submissionId)
      .then(setData)
      .catch(() => addToast("Could not load result.", "error"))
      .finally(() => setLoading(false));
  }, [submissionId]);

  return { data, loading };
}
