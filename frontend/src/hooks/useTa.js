// useTa.js — data hooks for the TA view: subjects, the two review tabs, one answer sheet, final marks.

import { useState, useEffect, useCallback } from "react";
import api from "../services/api";
import useToastStore from "../store/toastStore";

// The TA's subjects with the number of items waiting in each tab
export function useTaSubjects() {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToastStore();
  useEffect(() => {
    api.get("/ta/subjects")
      .then((res) => setSubjects(res.data))
      .catch(() => addToast("Could not load your subjects.", "error"))
      .finally(() => setLoading(false));
  }, [addToast]);
  return { subjects, loading };
}

// Pending items of one tab ("flagged" | "reevaluation") for one subject
export function useTaQueue(subject, tab) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const { addToast } = useToastStore();
  useEffect(() => {
    if (!subject) return;
    setLoading(true);
    api.get("/ta/queue", { params: { subject, tab } })
      .then((res) => setItems(res.data))
      .catch(() => addToast("Could not load the review queue.", "error"))
      .finally(() => setLoading(false));
  }, [subject, tab, addToast]);
  return { items, loading };
}

// Everything for one answer sheet (paper materials, questions with AI marks + reasons)
export function useTaItem(submissionId) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToastStore();
  const load = useCallback(() => {
    setLoading(true);
    api.get(`/ta/items/${submissionId}`)
      .then((res) => setData(res.data))
      .catch(() => addToast("Could not load this answer sheet.", "error"))
      .finally(() => setLoading(false));
  }, [submissionId, addToast]);
  useEffect(() => { if (submissionId) load(); }, [submissionId, load]);
  return { data, loading, reload: load };
}

// Send the TA's final marks (only changed questions) for one tab
export function useSubmitTaMarks() {
  const [saving, setSaving] = useState(false);
  const { addToast } = useToastStore();
  const submit = async (submissionId, body) => {
    setSaving(true);
    try {
      const res = await api.post(`/ta/items/${submissionId}/marks`, body);
      addToast("Marks submitted.", "success");
      return res.data;
    } catch (e) {
      addToast(e.response?.data?.detail || "Could not submit the marks.", "error");
      return null;
    } finally {
      setSaving(false);
    }
  };
  return { submit, saving };
}
