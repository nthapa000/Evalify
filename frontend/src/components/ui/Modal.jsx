// Modal.jsx — dialog on a dimmed page; closes on Escape, on the backdrop, or on "Close".

import { useEffect } from "react";

export default function Modal({ isOpen, onClose, title, children, footer }) {
  // Close on Escape key
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose?.(); };
    if (isOpen) document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    // Backdrop — click outside to close
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-paper-900/40 p-4"
         onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}>
      <div role="dialog" aria-label={title} className="bg-paper-50 border border-paper-900 rounded-sm w-full max-w-lg">
        {/* Header: serif title, text close button */}
        <div className="flex items-baseline justify-between px-5 py-3 border-b border-paper-300">
          <h2 className="font-serif text-lg text-paper-900">{title}</h2>
          <button onClick={onClose} aria-label="Close" className="kicker hover:text-paper-900">Close</button>
        </div>
        <div className="px-5 py-4">{children}</div>
        {/* Optional footer (action buttons) */}
        {footer && <div className="px-5 py-3 border-t border-paper-300 flex justify-end gap-2">{footer}</div>}
      </div>
    </div>
  );
}
