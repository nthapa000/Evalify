// mockData.js — in-memory mock state and async helpers.
// All hooks call these instead of real API endpoints in Phase 1 & 2.
// Replace each function with the real axios call in Phase 2.

// ── Seed Data ─────────────────────────────────────────────────────────────────

export const MOCK_TEACHER = {
  id: "t001",
  role: "teacher",
  name: "Prof. Ramesh Kumar",
  email: "teacher@evalify.local",
  password: "Teacher@123",
};

export const MOCK_STUDENTS = [
  { id: "s001", role: "student", name: "Aarav Sharma", roll_no: "CS2025001", password: "Student@123", subject: "Computer Science" },
  { id: "s002", role: "student", name: "Priya Mehta", roll_no: "CS2025002", password: "Student@123", subject: "Computer Science" },
  { id: "s003", role: "student", name: "Rohan Verma", roll_no: "MA2025001", password: "Student@123", subject: "Mathematics" },
];

// Mutable arrays so createPaper / submitAnswerSheet can push to them
let _papers = [
  {
    id: "p001",
    teacher_id: "t001",
    name: "CS101 — Midterm Exam",
    subject: "Computer Science",
    type: "mcq",
    typeLabel: "MCQ Only",
    totalMarks: 40,
    mcqCount: 20,
    mcqMarks: 2,
    mcqQuestionMarks: {},
    config: { negativeMaking: false },
    mcqAnswers: {
      Q1: "A", Q2: "B", Q3: "C", Q4: "D", Q5: "A", Q6: "B", Q7: "C", Q8: "D", Q9: "A", Q10: "B",
      Q11: "C", Q12: "D", Q13: "A", Q14: "B", Q15: "C", Q16: "D", Q17: "A", Q18: "B", Q19: "C", Q20: "D"
    },
    questionPaperUrl: null,
    answerKeyRefUrl: null,
    createdAt: "2026-04-10T09:00:00Z",
    resultCount: 2,
  },
  {
    id: "p002",
    teacher_id: "t001",
    name: "Physics — Unit Test 2",
    subject: "Physics",
    type: "mcq_numerical",
    typeLabel: "MCQ + Numerical",
    totalMarks: 30,
    mcqCount: 10,
    mcqMarks: 2,
    mcqQuestionMarks: {},
    numericalCount: 5,
    numericalMarks: 2,
    numericalQuestionMarks: {},
    config: {},
    mcqAnswers: { Q1: "B", Q2: "A", Q3: "C", Q4: "D", Q5: "B", Q6: "A", Q7: "C", Q8: "D", Q9: "B", Q10: "A" },
    numericalAnswers: {
      N1: { answer: 9.8, tolerance_type: "range", tolerance_value: 0.1 },
      N2: { answer: 3.14, tolerance_type: "decimal_variants", accepted_variants: ["3.14", "3.141", "π"] },
      N3: { answer: 100, tolerance_type: "exact" },
      N4: { answer: 0.5, tolerance_type: "range", tolerance_value: 0.05 },
      N5: { answer: 6.67, tolerance_type: "range", tolerance_value: 0.01 },
    },
    questionPaperUrl: null,
    answerKeyRefUrl: null,
    createdAt: "2026-04-12T11:00:00Z",
    resultCount: 1,
  },
  {
    id: "p003",
    teacher_id: "t001",
    name: "CS201 — Final Exam",
    subject: "Computer Science",
    type: "mcq_numerical_subjective",
    typeLabel: "MCQ + Numerical + Subjective",
    totalMarks: 60,
    mcqCount: 10,
    mcqMarks: 2,
    mcqQuestionMarks: {},
    numericalCount: 3,
    numericalMarks: 4,
    numericalQuestionMarks: {},
    subjectiveCount: 2,
    subjectiveMarks: 10,
    subjectiveQuestionMarks: {},
    config: {},
    mcqAnswers: { Q1: "A", Q2: "B", Q3: "C", Q4: "A", Q5: "D", Q6: "B", Q7: "C", Q8: "A", Q9: "D", Q10: "B" },
    numericalAnswers: {
      N1: { answer: 1024, tolerance_type: "exact" },
      N2: { answer: 0.693, tolerance_type: "range", tolerance_value: 0.01 },
      N3: { answer: 2, tolerance_type: "exact" },
    },
    subjectiveQuestions: [
      {
        id: "S1",
        question_text: "Explain the working of a transformer model.",
        max_marks: 10,
        rubric: {
          key_concepts: ["self-attention mechanism", "positional encoding", "encoder-decoder structure", "multi-head attention"],
          mandatory_concepts: ["self-attention mechanism"],
          marks_per_concept: 2.5,
          model_answer: "A transformer uses self-attention to process sequences in parallel...",
        },
      },
      {
        id: "S2",
        question_text: "What is backpropagation? Explain with an example.",
        max_marks: 10,
        rubric: {
          key_concepts: ["chain rule", "gradient descent", "loss function", "weight update"],
          mandatory_concepts: ["chain rule"],
          marks_per_concept: 2.5,
          model_answer: "Backpropagation computes gradients via the chain rule...",
        },
      },
    ],
    questionPaperUrl: null,
    answerKeyRefUrl: null,
    createdAt: "2026-04-15T14:00:00Z",
    resultCount: 0,
  },
];

// Submissions — links a student + paper to a result
let _submissions = [
  {
    id: "sub001",
    student_id: "s001",
    student_name: "Aarav Sharma",
    roll_no: "CS2025001",
    paper_id: "p001",
    paper_name: "CS101 — Midterm Exam",
    status: "evaluated",
    submittedAt: "2026-04-11T10:30:00Z",
    result: { mcqScore: 30, numericalScore: 0, subjectiveScore: 0, totalScore: 30, maxScore: 40, percentage: 75 },
  },
  {
    id: "sub002",
    student_id: "s002",
    student_name: "Priya Mehta",
    roll_no: "CS2025002",
    paper_id: "p001",
    paper_name: "CS101 — Midterm Exam",
    status: "evaluated",
    submittedAt: "2026-04-11T11:00:00Z",
    result: { mcqScore: 36, numericalScore: 0, subjectiveScore: 0, totalScore: 36, maxScore: 40, percentage: 90 },
  },
  {
    id: "sub003",
    student_id: "s001",
    student_name: "Aarav Sharma",
    roll_no: "CS2025001",
    paper_id: "p002",
    paper_name: "Physics — Unit Test 2",
    status: "evaluated",
    submittedAt: "2026-04-13T09:45:00Z",
    result: { mcqScore: 14, numericalScore: 6, subjectiveScore: 0, totalScore: 20, maxScore: 30, percentage: 67 },
  },
];

// ── Helper ────────────────────────────────────────────────────────────────────
const delay = (ms) => new Promise((r) => setTimeout(r, ms));

// ── Auth ──────────────────────────────────────────────────────────────────────
export async function mockLoginTeacher({ email, password }) {
  await delay(800);
  if (email === MOCK_TEACHER.email && password === MOCK_TEACHER.password) {
    return { token: "mock-teacher-jwt-token", user: { id: MOCK_TEACHER.id, name: MOCK_TEACHER.name, email, role: "teacher" } };
  }
  throw new Error("Invalid email or password.");
}

export async function mockLoginStudent({ roll_no, password }) {
  await delay(800);
  const student = MOCK_STUDENTS.find((s) => s.roll_no === roll_no && s.password === password);
  if (student) {
    return { token: "mock-student-jwt-token", user: { id: student.id, name: student.name, roll_no, role: "student" } };
  }
  throw new Error("Invalid roll number or password.");
}

// ── Papers ────────────────────────────────────────────────────────────────────
export async function mockGetTeacherPapers() {
  await delay(700);
  return [..._papers];
}

export async function mockGetPaper(id) {
  await delay(400);
  const paper = _papers.find((p) => p.id === id);
  if (!paper) throw new Error("Paper not found.");
  return { ...paper };
}

export async function mockCreatePaper(data) {
  await delay(1200);
  const paper = {
    ...data,
    id: `p${Date.now()}`,
    teacher_id: "t001",
    createdAt: new Date().toISOString(),
    resultCount: 0,
  };
  _papers.push(paper);
  return paper;
}

export async function mockDeletePaper(id) {
  await delay(500);
  _papers = _papers.filter((p) => p.id !== id);
}

// ── Results (teacher view) ────────────────────────────────────────────────────
export async function mockGetPaperResults(paperId) {
  await delay(600);
  const subs = _submissions.filter((s) => s.paper_id === paperId && s.status === "evaluated");
  const scores = subs.map((s) => s.result.totalScore);
  return {
    submissions: subs,
    stats: {
      average: scores.length ? +(scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : 0,
      highest: scores.length ? Math.max(...scores) : 0,
      lowest: scores.length ? Math.min(...scores) : 0,
      count: scores.length,
    },
  };
}

// ── Submissions ───────────────────────────────────────────────────────────────
export async function mockGetAvailablePapers(studentId) {
  await delay(600);
  // Return all papers with submission status for this student
  return _papers.map((p) => {
    const sub = _submissions.find((s) => s.student_id === studentId && s.paper_id === p.id);
    return { ...p, submissionStatus: sub ? sub.status : "not_submitted", submissionId: sub?.id ?? null };
  });
}

export async function mockSubmitAnswerSheet(paperId, studentId, studentName, rollNo) {
  await delay(1500);
  const paper = _papers.find((p) => p.id === paperId);
  const sub = {
    id: `sub${Date.now()}`,
    student_id: studentId,
    student_name: studentName,
    roll_no: rollNo,
    paper_id: paperId,
    paper_name: paper?.name ?? "",
    status: "processing",
    submittedAt: new Date().toISOString(),
    result: null,
  };
  _submissions.push(sub);
  // Simulate evaluation completing after 4 seconds
  setTimeout(() => {
    sub.status = "evaluated";
    const maxScore = paper?.totalMarks ?? 40;
    const totalScore = Math.round(maxScore * (0.5 + Math.random() * 0.45));
    sub.result = {
      mcqScore: Math.round(totalScore * 0.6),
      numericalScore: paper?.numericalCount ? Math.round(totalScore * 0.2) : 0,
      subjectiveScore: paper?.subjectiveCount ? Math.round(totalScore * 0.2) : 0,
      totalScore,
      maxScore,
      percentage: +((totalScore / maxScore) * 100).toFixed(1),
    };
    // Update paper result count
    const p = _papers.find((pp) => pp.id === paperId);
    if (p) p.resultCount = (_submissions.filter((s) => s.paper_id === paperId && s.status === "evaluated")).length;
  }, 4000);
  return sub;
}

export async function mockGetSubmissionStatus(submissionId) {
  await delay(300);
  const sub = _submissions.find((s) => s.id === submissionId);
  if (!sub) throw new Error("Submission not found.");
  return { id: sub.id, status: sub.status, result: sub.result };
}

// Aggregate scores for a paper to show avg/highest alongside student's result
export async function mockGetResult(submissionId) {
  await delay(400);
  const sub = _submissions.find((s) => s.id === submissionId);
  if (!sub || !sub.result) throw new Error("Result not available yet.");
  const paper = _papers.find((p) => p.id === sub.paper_id);
  const peerScores = _submissions
    .filter((s) => s.paper_id === sub.paper_id && s.status === "evaluated")
    .map((s) => s.result.totalScore);
  return {
    ...sub,
    paper,
    stats: {
      average: peerScores.length ? +(peerScores.reduce((a, b) => a + b, 0) / peerScores.length).toFixed(1) : sub.result.totalScore,
      highest: peerScores.length ? Math.max(...peerScores) : sub.result.totalScore,
    },
  };
}
