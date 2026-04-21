// authStore.js — Zustand store for authentication state.
// Token is persisted in localStorage so page refreshes don't log the user out.

import { create } from "zustand";

const _token = localStorage.getItem("evalify_token");
const _user  = (() => {
  try { return JSON.parse(localStorage.getItem("evalify_user") || "null"); }
  catch { return null; }
})();

const useAuthStore = create((set) => ({
  token: _token,
  user:  _user,

  setAuth: (token, user) => {
    localStorage.setItem("evalify_token", token);
    localStorage.setItem("evalify_user", JSON.stringify(user));
    set({ token, user });
  },

  clearAuth: () => {
    localStorage.removeItem("evalify_token");
    localStorage.removeItem("evalify_user");
    set({ token: null, user: null });
  },
}));

export default useAuthStore;
