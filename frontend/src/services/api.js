// api.js — single Axios instance used by every hook and component.
// Attaches the JWT token from Zustand authStore to every request automatically.

import axios from "axios";
import useAuthStore from "../store/authStore";

// VITE_API_BASE_URL is set at build time; falls back to Vite's dev proxy (/api)
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api",
  headers: { "Content-Type": "application/json" },
});

// Request interceptor: inject Bearer token before each request
api.interceptors.request.use((config) => {
  // Read token from Zustand store (kept in memory, never localStorage)
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
