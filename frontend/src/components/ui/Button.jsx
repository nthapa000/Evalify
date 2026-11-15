// Button.jsx — square, hairline buttons: solid ink for the main action, outlined for the rest.

// Colour scheme per variant
const VARIANTS = {
  primary:   "bg-paper-900 text-paper-50 hover:bg-ink-800 border border-paper-900",
  secondary: "bg-transparent text-paper-900 border border-paper-400 hover:border-paper-900 hover:bg-paper-50",
  danger:    "bg-pen-500 text-paper-50 border border-pen-500 hover:bg-pen-600",
  ghost:     "bg-transparent text-ink-600 border border-transparent underline underline-offset-4 decoration-ink-200 hover:decoration-ink-600",
};

// Padding / font size per size
const SIZES = {
  sm: "px-3 py-1.5 text-[13px]",
  md: "px-4 py-2 text-sm",
  lg: "px-5 py-2.5 text-sm",
};

export default function Button({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  disabled = false,
  className = "",
  ...props
}) {
  return (
    <button
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-sm font-medium tracking-wide
        disabled:opacity-40 disabled:cursor-not-allowed transition-colors duration-100
        ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    >
      {/* Thin progress bar instead of a spinner while loading */}
      {loading && <span aria-hidden className="w-3 h-3 border border-current border-r-transparent rounded-full animate-spin" />}
      {children}
    </button>
  );
}
