// Badge.jsx — small square status tag in mono capitals, outlined in the status colour.

// Colour per variant
const VARIANTS = {
  success: "border-moss-400 text-moss-700 bg-moss-50",
  warning: "border-ochre-400 text-ochre-700 bg-ochre-50",
  error:   "border-pen-300 text-pen-600 bg-pen-50",
  info:    "border-ink-300 text-ink-700 bg-ink-50",
  neutral: "border-paper-300 text-paper-600 bg-paper-50",
  indigo:  "border-ink-300 text-ink-700 bg-ink-50",
};

export default function Badge({ children, variant = "neutral", className = "" }) {
  return (
    <span className={`inline-flex items-center whitespace-nowrap px-1.5 py-px border rounded-sm font-mono text-[11px] uppercase tracking-wide ${VARIANTS[variant]} ${className}`}>
      {children}
    </span>
  );
}
