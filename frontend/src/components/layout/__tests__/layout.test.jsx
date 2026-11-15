// layout.test.jsx — navigation bar and side menu per role.
import { describe, it, expect } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderAt, loginAs } from "../../../test/utils";
import Sidebar from "../Sidebar";
import Navbar from "../Navbar";
import useAuthStore from "../../../store/authStore";

describe("layout", () => {
  // Why: a TA's menu leads to the TA dashboard, not to teacher or student pages
  it("Sidebar shows TA links for a TA", () => {
    loginAs("ta");
    renderAt(<Sidebar />);
    expect(screen.getByRole("link", { name: /Review queue/ })).toHaveAttribute("href", "/ta/dashboard");
    expect(screen.queryByRole("link", { name: /Create Paper/ })).toBeNull();
  });

  // Why: teachers keep their existing menu
  it("Sidebar shows teacher links for a teacher", () => {
    loginAs("teacher");
    renderAt(<Sidebar />);
    expect(screen.getByRole("link", { name: /Create Paper/ })).toBeInTheDocument();
  });

  // Why: signing out clears the session and returns to that role's own login page
  it("Navbar signs a TA out to the TA login", () => {
    loginAs("ta");
    renderAt(<Navbar />, { extra: { "/login/ta": <p>TA login page</p> } });
    fireEvent.click(screen.getByText("Sign out"));
    expect(screen.getByText("TA login page")).toBeInTheDocument();
    expect(useAuthStore.getState().token).toBeNull();
  });
});
