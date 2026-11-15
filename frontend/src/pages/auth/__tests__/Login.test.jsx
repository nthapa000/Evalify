// Login.test.jsx — the three login pages (teacher, student, TA).
import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderAt } from "../../../test/utils";
import useAuthStore from "../../../store/authStore";

vi.mock("../../../services/api", async () => ({ default: (await import("../../../test/mockApi")).makeApi() }));
import api from "../../../services/api";
import TeacherLogin from "../TeacherLogin";
import StudentLogin from "../StudentLogin";
import TaLogin from "../TaLogin";

beforeEach(() => {
  api.routes["POST /auth/ta/login"] = { token: "t", user: { name: "Rahul Menon", role: "ta", subjects: ["Computer Science"] } };
  api.routes["POST /auth/teacher/login"] = { token: "t", user: { name: "Prof. Ramesh Kumar", role: "teacher" } };
});

describe("Login pages", () => {
  // Why: TA is the new third role; logging in must store the session and open the TA dashboard
  it("TA login signs in and opens the TA dashboard", async () => {
    renderAt(<TaLogin />, { extra: { "/ta/dashboard": <p>TA home</p> } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "ta.cs1@evalify.local" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "Ta@12345" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));
    expect(await screen.findByText("TA home")).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith("/auth/ta/login", { email: "ta.cs1@evalify.local", password: "Ta@12345" });
    expect(useAuthStore.getState().user.role).toBe("ta");
  });

  // Why: an empty form shows a message instead of calling the server
  it("TA login validates the form", async () => {
    renderAt(<TaLogin />);
    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));
    expect(await screen.findByText("Email is required.")).toBeInTheDocument();
  });

  // Why: each login page links to the other two so users can find their own
  it("login pages link to each other", () => {
    renderAt(<TeacherLogin />);
    expect(screen.getByRole("link", { name: /Student Login/ })).toHaveAttribute("href", "/login/student");
    expect(screen.getByRole("link", { name: /TA Login/ })).toHaveAttribute("href", "/login/ta");
  });

  // Why: the existing teacher login still signs in and opens the teacher dashboard
  it("teacher login signs in", async () => {
    renderAt(<TeacherLogin />, { extra: { "/teacher/dashboard": <p>Teacher home</p> } });
    fireEvent.change(screen.getByPlaceholderText("teacher@evalify.local"), { target: { value: "teacher@evalify.local" } });
    fireEvent.change(screen.getByPlaceholderText("••••••••"), { target: { value: "Teacher@123" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));
    expect(await screen.findByText("Teacher home")).toBeInTheDocument();
  });

  // Why: the student login page renders its roll-number form
  it("student login renders", () => {
    renderAt(<StudentLogin />);
    expect(screen.getByRole("button", { name: /Sign In/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /TA Login/ })).toBeInTheDocument();
  });
});
