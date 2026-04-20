// useAuth.js — wraps the authStore with mock login/logout logic.
// Phase 2: replace mockLoginTeacher/Student with real axios calls.

import { useState } from "react";
import useAuthStore from "../store/authStore";
import { mockLoginTeacher, mockLoginStudent } from "../utils/mockData";
import useToastStore from "../store/toastStore";

export default function useAuth() {
  const { token, user, setAuth, clearAuth } = useAuthStore();
  const { addToast } = useToastStore();
  const [loading, setLoading] = useState(false);

  const loginTeacher = async (credentials) => {
    setLoading(true);
    try {
      const { token: tok, user: u } = await mockLoginTeacher(credentials);
      setAuth(tok, u);
      addToast(`Welcome back, ${u.name}!`, "success");
      return true;
    } catch (err) {
      addToast(err.message, "error");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const loginStudent = async (credentials) => {
    setLoading(true);
    try {
      const { token: tok, user: u } = await mockLoginStudent(credentials);
      setAuth(tok, u);
      addToast(`Welcome, ${u.name}!`, "success");
      return true;
    } catch (err) {
      addToast(err.message, "error");
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
