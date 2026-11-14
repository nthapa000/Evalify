// useAuth.js — teacher/student login and logout against the backend JWT API.

import { useState } from "react";
import useAuthStore from "../store/authStore";
import api from "../services/api";
import useToastStore from "../store/toastStore";

export default function useAuth() {
  const { token, user, setAuth, clearAuth } = useAuthStore();
  const { addToast } = useToastStore();
  const [loading, setLoading] = useState(false);

  // Shared login flow: POST credentials → store token + user → toast; returns success
  const login = async (path, credentials, greeting, failMsg) => {
    setLoading(true);
    try {
      const { data } = await api.post(path, credentials);
      setAuth(data.token, data.user);
      addToast(`${greeting}, ${data.user.name}!`, "success");
      return true;
    } catch (err) {
      addToast(err.response?.data?.detail || failMsg, "error");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const loginTeacher = (c) => login("/auth/teacher/login", c, "Welcome back", "Teacher login failed.");
  const loginStudent = (c) => login("/auth/student/login", c, "Welcome", "Student login failed.");

  // Clear the stored session
  const logout = () => {
    clearAuth();
    addToast("Signed out successfully.", "info");
  };

  return { user, token, isAuthenticated: !!token, loading, loginTeacher, loginStudent, logout };
}
