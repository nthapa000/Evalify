// formatters.js — display formatting helpers used across the UI.

export const formatDate = (iso) =>
  new Date(iso).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });

export const formatDateTime = (iso) =>
  new Date(iso).toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });

export const formatPercent = (n) => `${Number(n).toFixed(1)}%`;

// Returns "A" for >= 90, "B" for >= 75, etc.
export const gradeFromPercent = (pct) => {
  if (pct >= 90) return "A+";
  if (pct >= 80) return "A";
  if (pct >= 70) return "B";
  if (pct >= 60) return "C";
  if (pct >= 50) return "D";
  return "F";
};

// Human-readable label for paper type values from mockData
export const paperTypeLabel = (type) => ({
  mcq: "MCQ Only",
  mcq_numerical: "MCQ + Numerical",
  mcq_numerical_subjective: "MCQ + Numerical + Subjective",
}[type] ?? type);

export const statusLabel = (status) => ({
  not_submitted: "Not Submitted",
  processing:    "Processing",
  evaluated:     "Evaluated",
}[status] ?? status);
