// authStore.test.js — the logged-in session (token + user).
import { describe, it, expect } from "vitest";
import useAuthStore from "../authStore";

describe("authStore", () => {
  // Why: a page refresh must keep the user logged in, so the session is saved in localStorage
  it("saves and clears the session", () => {
    useAuthStore.getState().setAuth("t1", { name: "Rahul", role: "ta" });
    expect(useAuthStore.getState().user.role).toBe("ta");
    expect(localStorage.getItem("evalify_token")).toBe("t1");
    useAuthStore.getState().clearAuth();
    expect(useAuthStore.getState().token).toBeNull();
    expect(localStorage.getItem("evalify_user")).toBeNull();
  });
});
