// Toast.jsx — messages from toastStore, stacked bottom-left; a coloured rule marks the type.
// Mounted once in App.jsx so messages appear on every page.

import useToastStore from "../../store/toastStore";

// Left rule colour per message type
const RULE = { success: "border-l-moss-500", error: "border-l-pen-500", info: "border-l-ink-500" };

export default function ToastContainer() {
  const { toasts, removeToast } = useToastStore();

  return (
    <div className="fixed bottom-4 left-4 z-[100] space-y-2 pointer-events-none">
      {toasts.map((t) => (
        <div key={t.id} role="status"
             className={`pointer-events-auto flex items-start gap-4 bg-paper-900 text-paper-50 border-l-4 ${RULE[t.type] ?? RULE.info} rounded-sm px-4 py-3 max-w-sm`}>
          <p className="text-sm flex-1">{t.message}</p>
          <button onClick={() => removeToast(t.id)} aria-label="Dismiss" className="font-mono text-[11px] uppercase text-paper-400 hover:text-paper-50">
            Dismiss
          </button>
        </div>
      ))}
    </div>
  );
}
