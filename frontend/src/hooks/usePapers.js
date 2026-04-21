// usePapers.js — data access hook for exam papers.
// Phase 3: real API integration with Axios.

import { useState, useEffect, useCallback } from "react";
import api from "../services/api";
import useToastStore from "../store/toastStore";

// List all papers for the logged-in teacher
export function useTeacherPapers() {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToastStore();

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get("/papers");
      setPapers(res.data);
    } catch (e) {
      addToast("Failed to load papers.", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => { fetch(); }, [fetch]);
  return { papers, loading, refetch: fetch };
}

// Create a paper — returns the created paper on success
export function useCreatePaper() {
  const [loading, setLoading] = useState(false);
  const { addToast } = useToastStore();

  const createPaper = async (data) => {
    setLoading(true);
    try {
      const res = await api.post("/papers", data);
      addToast("Paper created successfully!", "success");
      return res.data;
    } catch (e) {
      addToast("Failed to create paper.", "error");
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { createPaper, loading };
}

// Fetch results for one paper (teacher view)
export function usePaperResults(paperId) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToastStore();

  useEffect(() => {
    if (!paperId) return;
    setLoading(true);
    api.get(`/results/paper/${paperId}`)
      .then(res => setData(res.data))
      .catch(() => addToast("Failed to load results.", "error"))
      .finally(() => setLoading(false));
  }, [paperId, addToast]);

  return { data, loading };
}

// Upload a PDF to the server — returns the persistent server URL or null
export function useUploadPaperFile() {
  const [uploading, setUploading] = useState(false);
  const { addToast } = useToastStore();

  const upload = async (file) => {
    if (!file) return null;
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await api.post("/papers/files/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return res.data.url;
    } catch (e) {
      addToast("Failed to upload PDF. Check file size (max 20 MB).", "error");
      return null;
    } finally {
      setUploading(false);
    }
  };

  return { upload, uploading };
}

// Extract MCQ answers from an already-uploaded answer key PDF
export function useExtractAnswers() {
  const [extracting, setExtracting] = useState(false);
  const { addToast } = useToastStore();

  const extract = async (fileUrl, mcqCount) => {
    if (!fileUrl || !mcqCount) return null;
    setExtracting(true);
    try {
      const res = await api.post("/papers/extract-answers", { file_url: fileUrl, mcq_count: mcqCount });
      return res.data;       // { answers, confidence, extracted_count, raw_text_preview }
    } catch (e) {
      addToast("Failed to extract answers from PDF.", "error");
      return null;
    } finally {
      setExtracting(false);
    }
  };

  return { extract, extracting };
}

// Extract rubric from two teacher-uploaded PDFs (Type 3 papers)
export function useExtractRubric() {
  const [extracting, setExtracting] = useState(false);
  const { addToast } = useToastStore();

  const extractRubric = async ({ detailedAnswerUrl, gradeRubricUrl, subjectiveCount }) => {
    if (!detailedAnswerUrl || !gradeRubricUrl || !subjectiveCount) return null;
    setExtracting(true);
    try {
      const res = await api.post("/papers/extract-rubric", {
        detailed_answer_url: detailedAnswerUrl,
        grade_rubric_url:    gradeRubricUrl,
        subjective_count:    subjectiveCount,
      });
      if (res.data.warning) {
        addToast(`Extraction completed with warnings: ${res.data.warning}`, "info");
      } else {
        addToast("Rubric extracted successfully!", "success");
      }
      return res.data;  // { subjective_questions, subjective_rubrics, warning }
    } catch (e) {
      addToast("Failed to extract rubric from PDFs.", "error");
      return null;
    } finally {
      setExtracting(false);
    }
  };

  return { extractRubric, extracting };
}

// Fetch a single paper by ID (for PaperView page)
export function usePaperView(paperId) {
  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToastStore();

  useEffect(() => {
    if (!paperId) return;
    setLoading(true);
    api.get(`/papers/${paperId}`)
      .then(res => setPaper(res.data))
      .catch(() => addToast("Failed to load paper details.", "error"))
      .finally(() => setLoading(false));
  }, [paperId, addToast]);

  return { paper, loading };
}
