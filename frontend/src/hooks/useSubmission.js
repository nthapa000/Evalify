// useSubmission.js — student-side data hook for submitting and checking results.
// Phase 3: real API integration with multipart file uploads.

import { useState, useEffect, useRef } from "react";
import api from "../services/api";
import useToastStore from "../store/toastStore";

// List all papers available to the student
export function useAvailablePapers() {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToastStore();

  useEffect(() => {
    setLoading(true);
    api.get("/papers/available")
      .then(res => setPapers(res.data))
      .catch(() => addToast("Failed to load available papers.", "error"))
      .finally(() => setLoading(false));
  }, [addToast]);

  return { papers, loading };
}

// Handle submission of an answer sheet image
// sheetType: "omr" (bubble sheet) | "handwritten" (written answers)
export function useSubmitAnswerSheet() {
  const [loading, setLoading] = useState(false);
  const { addToast } = useToastStore();

  const submit = async (paperId, files, sheetType = "omr") => {
    if (!files || files.length === 0) return null;
    setLoading(true);

    // Multipart form — one or more files under "files" key
    const formData = new FormData();
    const fileList = Array.isArray(files) ? files : [files];
    fileList.forEach((f) => formData.append("files", f));

    try {
      const res = await api.post(
        `/submissions?paper_id=${paperId}&sheet_type=${sheetType}`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      addToast("Answer sheet submitted. It is evaluated when your teacher starts the evaluation.", "info");
      return res.data;
    } catch (e) {
      addToast("Submission failed. Check your connection or file size.", "error");
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { submit, loading };
}

// Poll submission status until it reaches "evaluated"
export function useSubmissionStatus(submissionId) {
  const [status, setStatus] = useState("loading");
  const [result, setResult] = useState(null);
  const intervalRef = useRef();
  const { addToast } = useToastStore();

  useEffect(() => {
    if (!submissionId) return;

    const poll = async () => {
      try {
        const res = await api.get(`/submissions/${submissionId}/status`);
        const { status: s, result: r } = res.data;
        setStatus(s);

        if (s === "evaluated") {
          setResult(r);
          clearInterval(intervalRef.current);
        } else if (s === "awaiting_release" || s === "submitted") {
          // Marked (results come at release) or stored until the teacher starts evaluation: stop polling
          clearInterval(intervalRef.current);
        } else if (s === "error") {
          addToast("Evaluation failed. Please try re-uploading.", "error");
          clearInterval(intervalRef.current);
        }
      } catch (err) {
        // Only stop polling on hard 404s/auth errors
        if (err.response?.status === 404) {
          clearInterval(intervalRef.current);
        }
      }
    };

    poll(); // initial check
    intervalRef.current = setInterval(poll, 2000);
    return () => clearInterval(intervalRef.current);
  }, [submissionId, addToast]);

  return { status, result };
}

// Fetch the full result object for a completed submission (setData lets the page update it after actions)
export function useResult(submissionId) {
  const [data, setData] = useState(null);
  const [notReleased, setNotReleased] = useState(false);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToastStore();

  useEffect(() => {
    if (!submissionId) return;
    setLoading(true);
    api.get(`/results/${submissionId}`)
      .then(res => setData(res.data))
      .catch((e) => {
        // 409 = not released yet: the page shows "being evaluated", no error
        if (e.response?.status === 409) setNotReleased(true);
        else addToast("Could not load result details.", "error");
      })
      .finally(() => setLoading(false));
  }, [submissionId, addToast]);

  return { data, loading, setData, notReleased };
}

// The student's one re-evaluation request for a paper (remark says which questions and why)
export function useRequestReevaluation() {
  const [sending, setSending] = useState(false);
  const { addToast } = useToastStore();
  const request = async (submissionId, remark) => {
    setSending(true);
    try {
      const res = await api.post(`/submissions/${submissionId}/reevaluation`, { remark });
      addToast("Re-evaluation requested. A TA will check it.", "success");
      return res.data.reevaluation;
    } catch (e) {
      addToast(e.response?.data?.detail || "Could not send the request.", "error");
      return null;
    } finally {
      setSending(false);
    }
  };
  return { request, sending };
}
