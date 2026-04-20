// Toast.jsx — renders the toast queue from toastStore in the top-right corner.
// Mount this once in App.jsx so toasts appear globally across all pages.

import useToastStore from "../../store/toastStore";

const ICONS = {
  success: "✓",
  error:   "✕",
  info:    "i",
};

const COLORS = {
  success: "bg-green-600",
  error:   "bg-red-600",
  info:    "bg-indigo-600",
};

export default function ToastContainer() {
  const { toasts, removeToast } = useToastStore();

  return (
    <div className="fixed top-4 right-4 z-[100] space-y-2 pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="pointer-events-auto flex items-start gap-3 bg-white border border-gray-200 rounded-xl shadow-lg px-4 py-3 max-w-sm animate-fade-in"
        >
          {/* Colored type indicator dot */}
          <span className={`mt-0.5 flex-shrink-0 w-5 h-5 rounded-full text-white text-xs flex items-center justify-center font-bold ${COLORS[t.type]}`}>
            {ICONS[t.type]}
          </span>
          <p className="text-sm text-gray-700 flex-1">{t.message}</p>
          <button
            onClick={() => removeToast(t.id)}
            className="text-gray-400 hover:text-gray-600 text-xs mt-0.5"
          >✕</button>
        </div>
      ))}
    </div>
  );
}
