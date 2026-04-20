// api.js — single Axios instance used by every hook and component.
// Attaches the JWT token from Zustand authStore to every request automatically.
// Phase 0: instance created; interceptors will be wired in Phase 2 when auth is built.

import axios from "axios";

// VITE_API_BASE_URL is set at build time; falls back to Vite's dev proxy (/api)
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api",
  headers: { "Content-Type": "application/json" },
});

// Request interceptor: inject Bearer token before each request
api.interceptors.request.use((config) => {
  // Token is stored in memory (Zustand store), never in localStorage
  const token = window.__evalify_token__;   // placeholder; replaced by authStore in Phase 2
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
