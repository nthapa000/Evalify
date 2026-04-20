// authStore.js — Zustand store for authentication state.
// Token is kept in memory only (not localStorage) to prevent XSS token theft.
// Phase 0: stub; login/logout actions implemented in Phase 2.

import { create } from "zustand";

const useAuthStore = create((set) => ({
  token: null,       // JWT string; null = not logged in
  user: null,        // { id, role, name, email/roll_no }

  setAuth: (token, user) => set({ token, user }),
  clearAuth: () => set({ token: null, user: null }),
}));

export default useAuthStore;
