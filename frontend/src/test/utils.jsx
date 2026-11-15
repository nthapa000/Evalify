// utils.jsx — test helpers: render inside a router and log in as a given role.
import { render } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import useAuthStore from "../store/authStore";

// Render a page at a URL; extra routes record where the page navigated to
export function renderAt(ui, { path = "/", route = "/", extra = {} } = {}) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path={path} element={ui} />
        {Object.entries(extra).map(([p, el]) => <Route key={p} path={p} element={el} />)}
      </Routes>
    </MemoryRouter>
  );
}

// Put a logged-in user in the auth store
export function loginAs(role, extra = {}) {
  const user = { id: "u1", name: `Test ${role}`, role, subjects: ["Computer Science"], ...extra };
  useAuthStore.getState().setAuth("token-123", user);
  return user;
}
