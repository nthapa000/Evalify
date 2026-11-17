// validators.js — pure validation functions used by login forms and paper creation.

export const isValidEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);

export const isValidRollNo = (v) => /^[A-Z]{2}\d{7}$/.test(v);

// Password must be 6+ chars with at least one letter and one digit
export const isValidPassword = (v) => v.length >= 6 && /[a-zA-Z]/.test(v) && /\d/.test(v);

export const isNonEmpty = (v) => typeof v === "string" && v.trim().length > 0;

export const isPositiveNumber = (v) => !isNaN(v) && Number(v) > 0;

// Returns an error string or empty string
export function validateTeacherLogin({ email, password }) {
  if (!isNonEmpty(email)) return "Email is required.";
  if (!isValidEmail(email)) return "Enter a valid email address.";
  if (!isNonEmpty(password)) return "Password is required.";
  return "";
}

export function validateStudentLogin({ roll_no, password }) {
  if (!isNonEmpty(roll_no)) return "Roll number is required.";
  if (!isNonEmpty(password)) return "Password is required.";
  return "";
}

// MCQ-only OMR paper: the blank OMR sheet is compulsory and its bubbles must be confirmed (the template is only used
// for marking once confirmed), so the wizard holds the teacher at step 3 until both are done
export const omrTemplateIncomplete = (form) =>
  form.type === "mcq" && form.answerSheetFormat === "omr" && !(form.omrTemplate?.bubbles?.length && form.omrTemplate.confirmed);
