// usePapers.js — data access hook for exam papers.
// Phase 2: swap mock* functions for real api.get / api.post calls.

import { useState, useEffect, useCallback } from "react";
import { mockGetTeacherPapers, mockCreatePaper, mockDeletePaper, mockGetPaper, mockGetPaperResults } from "../utils/mockData";
import useToastStore from "../store/toastStore";

// List all papers for the logged-in teacher
export function useTeacherPapers() {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToastStore();

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      setPapers(await mockGetTeacherPapers());
    } catch (e) {
      addToast("Failed to load papers.", "error");
    } finally {
      setLoading(false);
    }
  }, []);

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
      const paper = await mockCreatePaper(data);
      addToast("Paper created successfully!", "success");
      return paper;
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
    mockGetPaperResults(paperId)
      .then(setData)
      .catch(() => addToast("Failed to load results.", "error"))
      .finally(() => setLoading(false));
  }, [paperId]);

  return { data, loading };
}

// Fetch a single paper by ID (for PaperView page)
export function usePaperView(paperId) {
  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToastStore();

  useEffect(() => {
    if (!paperId) return;
    setLoading(true);
    mockGetPaper(paperId)
      .then(setPaper)
      .catch(() => addToast("Failed to load paper details.", "error"))
      .finally(() => setLoading(false));
  }, [paperId]);

  return { paper, loading };
}
