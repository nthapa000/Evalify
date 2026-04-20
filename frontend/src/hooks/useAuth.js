// useAuth.js — handles login/logout using real API calls to the backend.
// Phase 3: real JWT authentication.

import { useState } from "react";
import useAuthStore from "../store/authStore";
import api from "../services/api";
import useToastStore from "../store/toastStore";

export default function useAuth() {
  const { token, user, setAuth, clearAuth } = useAuthStore();
  const { addToast } = useToastStore();
  const [loading, setLoading] = useState(false);

  const loginTeacher = async (credentials) => {
    setLoading(true);
    try {
      const res = await api.post("/auth/teacher/login", credentials);
      const { token: tok, user: u } = res.data;
      setAuth(tok, u);
      addToast(`Welcome back, ${u.name}!`, "success");
      return true;
    } catch (err) {
      const msg = err.response?.data?.detail || "Teacher login failed.";
      addToast(msg, "error");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const loginStudent = async (credentials) => {
    setLoading(true);
    try {
      const res = await api.post("/auth/student/login", credentials);
      const { token: tok, user: u } = res.data;
      setAuth(tok, u);
      addToast(`Welcome, ${u.name}!`, "success");
      return true;
    } catch (err) {
      const msg = err.response?.data?.detail || "Student login failed.";
      addToast(msg, "error");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    clearAuth();
    addToast("Signed out successfully.", "info");
  };

  return {
    user,
    token,
    isAuthenticated: !!token,
    loading,
    loginTeacher,
    loginStudent,
    logout,
  };
}
