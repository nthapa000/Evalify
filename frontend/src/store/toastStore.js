// toastStore.js — Zustand store for toast notifications.
// Components import useToast() to show success/error/info messages.

import { create } from "zustand";

let _id = 0;

const useToastStore = create((set) => ({
  toasts: [],

  // type: "success" | "error" | "info"
  addToast: (message, type = "info") => {
    const id = ++_id;
    set((s) => ({ toasts: [...s.toasts, { id, message, type }] }));
    // Auto-dismiss after 4 seconds
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 4000);
  },

  removeToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

export default useToastStore;
