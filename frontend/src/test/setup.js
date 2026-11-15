// setup.js — runs before every frontend test: DOM matchers and a clean store/localStorage per test.
import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup, configure } from "@testing-library/react";

// The shared cluster machine is slow; give async UI updates more time than the 1 s default
configure({ asyncUtilTimeout: 4000 });

// Each test starts with an empty DOM and no saved login
afterEach(() => {
  cleanup();
  localStorage.clear();
});
