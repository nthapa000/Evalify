// validators.test.js — login and form validation rules.
import { describe, it, expect } from "vitest";
import { isValidEmail, isValidRollNo, isValidPassword, isNonEmpty, isPositiveNumber,
         validateTeacherLogin, validateStudentLogin } from "../validators";

describe("validators", () => {
  // Why: teacher and TA logins are by email; obviously wrong emails are caught before calling the server
  it("checks emails", () => {
    expect(isValidEmail("ta.cs1@evalify.local")).toBe(true);
    expect(isValidEmail("not-an-email")).toBe(false);
  });

  // Why: every roll number generated from demo.env (e.g. DS2025049) must pass the roll-number format
  it("accepts demo.env roll numbers", () => {
    expect(["CS2025001", "PH2025020", "DS2025049"].every(isValidRollNo)).toBe(true);
    expect(isValidRollNo("cs2025001")).toBe(false);
  });

  // Why: basic field checks used by the paper wizard
  it("checks passwords, non-empty and positive numbers", () => {
    expect(isValidPassword("Teacher@123")).toBe(true);
    expect(isValidPassword("short")).toBe(false);
    expect(isNonEmpty("  ")).toBe(false);
    expect(isPositiveNumber("2")).toBe(true);
    expect(isPositiveNumber("-1")).toBe(false);
  });

  // Why: the login pages show these messages instead of sending empty forms
  it("validates login forms", () => {
    expect(validateTeacherLogin({ email: "", password: "x" })).toBe("Email is required.");
    expect(validateTeacherLogin({ email: "a@b.co", password: "" })).toBe("Password is required.");
    expect(validateTeacherLogin({ email: "a@b.co", password: "x" })).toBe("");
    expect(validateStudentLogin({ roll_no: "", password: "x" })).toBe("Roll number is required.");
  });
});
