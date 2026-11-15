// App.test.jsx — role-based routing: each role reaches only its own pages.
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { loginAs } from "../test/utils";

vi.mock("../services/api", async () => {
  const api = (await import("../test/mockApi")).makeApi({ "GET /ta/subjects": [], "GET /papers": [], "GET /papers/available": [] });
  return { default: api };
});
import App from "../App";

const at = (route) => render(<MemoryRouter initialEntries={[route]}><App /></MemoryRouter>);

describe("App routing", () => {
  // Why: someone not logged in who opens a TA page must land on the TA login
  it("sends logged-out users to the right login", async () => {
    at("/ta/dashboard");
    expect(await screen.findByRole("heading", { name: "TA Login" })).toBeInTheDocument();
  });

  // Why: a TA opening a teacher page is sent back to the TA dashboard
  it("keeps a TA out of teacher pages", async () => {
    loginAs("ta");
    at("/teacher/dashboard");
    expect(await screen.findByRole("heading", { name: /Answer sheets to review/ })).toBeInTheDocument();
  });

  // Why: a student opening a TA page is sent to the student dashboard
  it("keeps a student out of TA pages", async () => {
    loginAs("student");
    at("/ta/dashboard");
    expect(await screen.findByText(/Welcome, Test student/)).toBeInTheDocument();
  });

  // Why: unknown URLs show a 404 page
  it("shows 404 for unknown pages", () => {
    at("/nope");
    expect(screen.getByText("404")).toBeInTheDocument();
  });
});
