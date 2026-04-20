# Phase 1 — Frontend Shell

## Goal
Build the complete React UI with mock data so every page, route, and user flow can be verified before any backend or ML code is written.

---

## What Was Done in Phase 1

| Area | Files Created |
|------|--------------|
| Utilities | `mockData.js`, `validators.js`, `formatters.js` |
| Stores | `authStore.js` (Phase 0), `toastStore.js` |
| UI Components | `Button`, `Card`, `Modal`, `Badge`, `Skeleton`, `Toast` |
| Form Components | `UploadZone`, `StepWizard`, `RubricBuilder` |
| Layout | `Navbar`, `Sidebar`, `PageWrapper` |
| Hooks | `useAuth`, `usePapers`, `useSubmission` |
| Auth Pages | `TeacherLogin`, `StudentLogin` |
| Teacher Pages | `Dashboard`, `CreatePaper` (5-step wizard), `PaperResults` |
| Student Pages | `Dashboard`, `SubjectPage`, `Submission`, `Result` |
| Router | `App.jsx` — full routing + role-based guards |

**Total: 32 JSX/JS source files · 253 KB JS bundle · 23 KB CSS bundle**

---

## Complete User Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         BROWSER                                  │
│                                                                  │
│  URL: /   ──► RootRedirect ──► /login/teacher  (not logged in)   │
│              OR               ──► /teacher/dashboard (teacher)   │
│                               ──► /student/dashboard (student)   │
└──────────────────────────────────────────────────────────────────┘

TEACHER FLOW
─────────────────────────────────────────────────────────────────
/login/teacher
  │  email + password → useAuth.loginTeacher() → mock 800ms delay
  │  ✓ → setAuth(token, user) in Zustand
  ▼
/teacher/dashboard
  │  useTeacherPapers() → mockGetTeacherPapers() → 3 seed papers
  │  Grid of PaperCards (type badge, marks, result count)
  ├─► "View Results" → /teacher/papers/:paperId/results
  │       usePaperResults() → stats bar + submissions table
  └─► "+ Create Paper" → /teacher/papers/create
          Step 1: Select type (MCQ / MCQ+Num / MCQ+Num+Sub)
          Step 2: Paper name, subject, question counts, marks
          Step 3: Enter MCQ answers (A/B/C/D buttons)
                  Enter numerical answers + tolerance config
          Step 4: Negative marking toggle
                  (Type 3) Subjective question text + RubricBuilder
          Step 5: Review summary
          ✓ → mockCreatePaper() → Success Modal → /teacher/dashboard

STUDENT FLOW
─────────────────────────────────────────────────────────────────
/login/student
  │  roll_no + password → useAuth.loginStudent() → mock 800ms delay
  ▼
/student/dashboard
  │  useAvailablePapers() → subject paper counts
  │  4 subject cards (CS / Math / Physics / Chemistry)
  │  Overview stats: total / pending / evaluated
  ▼
/student/subjects/:subject
  │  Papers filtered by subject with submission status badge
  ├─► "Upload Answer Sheet" → /student/submit/:paperId
  │       UploadZone (drag-and-drop image)
  │       Submit → mockSubmitAnswerSheet() → status: "processing"
  │       Polling every 2s via useSubmissionStatus()
  │       4s later status → "evaluated"
  │       Auto-redirect → /student/results/:submissionId
  └─► "View Result" (already evaluated)
          ▼
/student/results/:submissionId
  Score circle + grade badge
  Class average / highest
  Section breakdown (MCQ / Numerical / Subjective)
```

---

## Route Map

| Path | Component | Guard |
|------|-----------|-------|
| `/` | RootRedirect | — |
| `/login/teacher` | TeacherLogin | PublicOnly (redirect if logged in) |
| `/login/student` | StudentLogin | PublicOnly |
| `/teacher/dashboard` | teacher/Dashboard | teacher role |
| `/teacher/papers/create` | CreatePaper | teacher role |
| `/teacher/papers/:id/results` | PaperResults | teacher role |
| `/student/dashboard` | student/Dashboard | student role |
| `/student/subjects/:subject` | SubjectPage | student role |
| `/student/submit/:paperId` | Submission | student role |
| `/student/results/:submissionId` | Result | student role |
| `*` | 404 inline | — |

---

## File-by-File Purpose

### `src/utils/mockData.js`
Central in-memory data store for Phase 1 & 2.
- Exports `MOCK_TEACHER`, `MOCK_STUDENTS`, and mutable `_papers` / `_submissions` arrays.
- Every async helper (`mockLoginTeacher`, `mockGetTeacherPapers`, `mockSubmitAnswerSheet` etc.) adds an artificial delay with `setTimeout` to simulate real network latency.
- `mockSubmitAnswerSheet` schedules a `setTimeout` after 4s that flips `submission.status = "evaluated"` and generates a random score — this is what `useSubmissionStatus`'s poll loop detects.
- **Phase 2 replacement:** swap each `mock*` call with the corresponding `api.get` / `api.post` call in the hooks.

### `src/store/authStore.js`
Zustand store holding `{ token, user }` in JavaScript memory only.
Never persisted to `localStorage` — prevents XSS token theft.
On page refresh the user is logged out (acceptable trade-off for an academic tool).

### `src/store/toastStore.js`
Zustand store with a `toasts[]` array.
`addToast(message, type)` pushes a toast and auto-removes it after 4 seconds.
`<ToastContainer />` (mounted in `App.jsx`) renders them in the top-right corner.

### `src/components/ui/Button.jsx`
Four variants: `primary` (indigo), `secondary` (white border), `danger` (red), `ghost`.
Shows an inline spinner when `loading={true}` — prevents double-clicks during async actions.

### `src/components/ui/Card.jsx`
White rounded container with sub-components `Card.Header`, `Card.Body`, `Card.Footer` for consistent section spacing across all pages.

### `src/components/ui/Modal.jsx`
Focus-trapped overlay. Closes on Escape key or clicking the backdrop.
Used for the CreatePaper success confirmation and delete confirmations (future).

### `src/components/ui/Skeleton.jsx`
`SkeletonCard` — mimics a paper card shape while data is loading.
`SkeletonRow` — mimics a table row.
Used instead of spinners to avoid layout shifts.

### `src/components/ui/Toast.jsx`
Consumes `toastStore` and renders stacked notification pills in the top-right corner. Each toast auto-dismisses after 4s.

### `src/components/forms/UploadZone.jsx`
Drag-and-drop file zone. Generates a local object URL for image preview immediately after file selection. Used by both the teacher's answer-key step and the student's submission page.

### `src/components/forms/StepWizard.jsx`
Horizontal row of numbered circles with connector lines.
Completed steps show a `✓`. Active step has a ring highlight.
Driven by `current` prop from `CreatePaper`'s step state.

### `src/components/forms/RubricBuilder.jsx`
Per-subjective-question form for Type 3 papers (Step 4 of CreatePaper).
Tags for key concepts (press Enter or click Add), ★ toggles mandatory status, model answer textarea.
Calls `onChange(rubric)` on every change so CreatePaper accumulates all rubrics in `form.subjectiveRubrics[]`.

### `src/components/layout/Navbar.jsx`
Top bar: Evalify logo, user name + role, initials avatar, "Sign out" button.
Sign out calls `clearAuth()` then navigates to the appropriate login page.

### `src/components/layout/Sidebar.jsx`
Left panel with `NavLink` items. Active link gets indigo highlight.
Teacher sees: Dashboard, Create Paper.
Student sees: Dashboard.

### `src/components/layout/PageWrapper.jsx`
Full-viewport shell: Navbar (top) + Sidebar (left) + scrollable `<main>` (right).
Every authenticated page is wrapped in this.

### `src/hooks/useAuth.js`
Wraps `authStore` with `loginTeacher`, `loginStudent`, and `logout`.
Calls mock functions in Phase 1; will call `api.post("/auth/teacher/login")` in Phase 2.
Shows success/error toasts via `toastStore`.

### `src/hooks/usePapers.js`
Three exports:
- `useTeacherPapers()` — fetches paper list on mount, returns `{ papers, loading, refetch }`.
- `useCreatePaper()` — returns `{ createPaper(data), loading }`.
- `usePaperResults(paperId)` — fetches submissions + stats for one paper.

### `src/hooks/useSubmission.js`
Four exports:
- `useAvailablePapers()` — papers for student with submission status overlay.
- `useSubmitAnswerSheet()` — POSTs answer sheet, returns submission object.
- `useSubmissionStatus(id)` — polls every 2s until `status === "evaluated"`.
- `useResult(id)` — fetches full result object including peer stats.

### `src/pages/auth/TeacherLogin.jsx` & `StudentLogin.jsx`
Login forms with inline error messages.
`PublicOnlyRoute` in App.jsx redirects already-authenticated users away from these pages.
Dev credentials shown on-screen for demo convenience (remove before production).

### `src/pages/teacher/Dashboard.jsx`
Grid of `PaperCard` components. Shows skeleton cards while `useTeacherPapers` is loading.
Each card: paper name, subject, type badge, total marks, question count, result count.

### `src/pages/teacher/CreatePaper.jsx`
5-step wizard controlled by local `step` state (1–5) and a single `form` object.

| Step | Component | Purpose |
|------|-----------|---------|
| 1 | `Step1` | Pick paper type — three clickable type cards |
| 2 | `Step2` | Enter name, subject, question counts and marks-per-question |
| 3 | `Step3` | A/B/C/D answer buttons for MCQ; answer + tolerance for Numerical |
| 4 | `Step4` | Negative marking toggle; `RubricBuilder` per subjective question |
| 5 | `Step5` | Read-only summary before final submission |

On submit → `mockCreatePaper()` → success modal → redirect to dashboard.

### `src/pages/teacher/PaperResults.jsx`
Stats bar (count / average / highest / lowest) above a sortable results table.
Shows skeleton rows while `usePaperResults` loads. Empty state message if no submissions.

### `src/pages/student/Dashboard.jsx`
4 subject cards (Computer Science / Mathematics / Physics / Chemistry).
Each shows how many papers are available for that subject.
Overview stats row at the bottom.

### `src/pages/student/SubjectPage.jsx`
Filters `useAvailablePapers()` to the current subject.
Each paper shows its submission status badge and the appropriate action button
(Upload / Evaluating… / View Result).

### `src/pages/student/Submission.jsx`
Two states:
1. **Before submit:** `UploadZone` + submit button (disabled until file selected). Tips box for good scan quality.
2. **After submit:** Loading animation with bouncing clock emoji + pulsing dots. Polls `useSubmissionStatus` every 2s and auto-navigates to Result page once `status === "evaluated"`.

### `src/pages/student/Result.jsx`
Score circle (score/max in a CSS-only ring), grade badge.
Three stat boxes: your score / class average / highest.
Section breakdown table (MCQ / Numerical / Subjective rows) based on paper type.

---

## Mock Data Flow

```
Browser session start
        │
        ▼
mockData.js module loaded (in-memory state initialised)
        │
        ├── _papers[]    ← 3 seed papers (MCQ, MCQ+Num, MCQ+Num+Sub)
        └── _submissions[] ← 3 seed evaluated results

Teacher login (teacher@evalify.local / Teacher@123)
        → returns { token, user: { role:"teacher" } }
        → authStore.setAuth()

Student login (CS2025001 / Student@123)
        → returns { token, user: { role:"student" } }
        → authStore.setAuth()

Student submits answer sheet
        → _submissions.push({ status:"processing", ... })
        → setTimeout 4s → sub.status = "evaluated", result computed
        → useSubmissionStatus poll detects change
        → navigate to /student/results/:id
```

---

## How to Start Phase 1 Dev Server

```bash
# Ensure node wrapper is on PATH (one-time after login)
export PATH="$HOME/.local/bin:$PATH"

# Start Vite dev server
cd frontend
npm run dev
# → http://localhost:5173

# Teacher demo:  teacher@evalify.local / Teacher@123
# Student demo:  CS2025001 / Student@123
```

---

## Green Signal #1 Checklist

| Check | Result |
|-------|--------|
| All 10 routes render (no 404 or blank page) | ✅ |
| Teacher login redirects to /teacher/dashboard | ✅ |
| Student login redirects to /student/dashboard | ✅ |
| CreatePaper wizard completes all 5 steps | ✅ |
| Success modal appears after paper creation | ✅ |
| PaperResults shows stats + table | ✅ |
| Student dashboard shows subject cards | ✅ |
| Submission page polls and auto-navigates | ✅ |
| Result page shows score + breakdown | ✅ |
| Skeleton loaders visible during mock delay | ✅ |
| Toast notifications on login/logout/create | ✅ |
| Route guards block wrong-role access | ✅ |
| `npm run build` produces zero errors | ✅ |

---

## Phase Checklist

| Phase | Status |
|-------|--------|
| **Phase 0** | ✅ Done |
| **Phase 1** | ✅ Done |
| Phase 2 | Backend API + MongoDB + JWT auth |
| Phase 3 | Type 1 MCQ evaluation (OMR + TrOCR) |
| Phase 4 | Type 2 MCQ + Numerical (tolerance grading) |
| Phase 5 | Type 3 Subjective + LLM + MLflow |
| Phase 6 | Docker containerisation |
| Phase 7 | Kubernetes deployment |
| Phase 8 | Production deploy |
