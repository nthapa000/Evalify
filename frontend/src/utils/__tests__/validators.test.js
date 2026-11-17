// validators.test.js — login and form validation rules.
import { describe, it, expect } from "vitest";
import { isValidEmail, isValidRollNo, isValidPassword, isNonEmpty, isPositiveNumber, omrTemplateIncomplete,
         validateTeacherLogin, validateStudentLogin } from "../validators";

describe("validators", () => {
  // Why: teacher and TA logins are by email; obviously wrong emails are caught before calling the server
  it("checks emails", () => {
    expect(isValidEmail("ta.cs1@evalify.local")).toBe(true);
    expect(isValidEmail("not-an-email")).toBe(false);
  });

  // Why: every roll number generated from demo.env (e.g. DS2025048) must pass the roll-number format
  it("accepts demo.env roll numbers", () => {
    expect(["CS2025001", "PH2025020", "DS2025048"].every(isValidRollNo)).toBe(true);
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

// Why: user decisions (17 Nov) — an OMR paper needs its blank sheet, and the template is only used for marking once
// the teacher confirmed its bubbles, so the wizard holds the teacher at step 3 until both are done
describe("omrTemplateIncomplete", () => {
  const tpl = (confirmed) => ({ type: "mcq", answerSheetFormat: "omr", omrTemplate: { bubbles: [{}], confirmed } });
  it("blocks an OMR paper without a template or with an unconfirmed one", () => {
    expect(omrTemplateIncomplete({ type: "mcq", answerSheetFormat: "omr", omrTemplate: null })).toBe(true);
    expect(omrTemplateIncomplete(tpl(false))).toBe(true);
    expect(omrTemplateIncomplete(tpl(true))).toBe(false);
  });
  it("does not apply to handwritten papers or other paper types", () => {
    expect(omrTemplateIncomplete({ type: "mcq", answerSheetFormat: "handwritten", omrTemplate: null })).toBe(false);
    expect(omrTemplateIncomplete({ type: "mcq_numerical", answerSheetFormat: "omr", omrTemplate: null })).toBe(false);
  });
});
