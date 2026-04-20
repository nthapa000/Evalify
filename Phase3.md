# Phase 3 — MCQ Evaluation (OMR + TrOCR)

## Goal
Evaluate Type 1 MCQ exam papers automatically by detecting student answers from uploaded answer-sheet images.  
Two recognition paths are supported, and the student explicitly chooses which one applies to their sheet.

---

## What Changed in Phase 3

| Area | Files Modified |
|------|---------------|
| Backend service | `app/services/omr_engine.py` (rewritten) |
| Backend service | `app/services/trocr_engine.py` (rewritten) |
| Backend service | `app/services/evaluator.py` (rewritten) |
| Backend router  | `app/routers/submissions.py` (added `sheet_type` param) |
| Backend model   | `app/models/submission.py` (added `sheet_type` field) |
| Frontend hook   | `src/hooks/useSubmission.js` (passes `sheetType`) |
| Frontend page   | `src/pages/student/Submission.jsx` (sheet-type selector step) |

---

## Two-Engine Architecture

```
Student uploads answer sheet
        │
        ├── sheet_type = "omr"
        │       │
        │       └──► OMREngine (OpenCV)
        │               • Grayscale → Gaussian blur → adaptive threshold
        │               • Find bubble-like contours (size + aspect ratio filter)
        │               • Cluster contours into rows (Y-coordinate grouping)
        │               • Per row: pick the bubble with the most filled pixels
        │               • Returns { Q1:"A", Q2:"C", ... }
        │
        └── sheet_type = "handwritten"
                │
                └──► TrOCREngine
                        REAL mode  (torch + transformers installed)
                          • microsoft/trocr-base-handwritten model
                          • Runs on CPU or CUDA
                          • Returns raw OCR text + confidence score
                        STUB mode  (libraries missing)
                          • Returns empty answer map, flagged in result
                          • Pipeline still completes without crashing
                        Parser: regex "Q?(\d+)[. :)]\s*([A-D])" on OCR text
```

---

## Full Evaluation Flow

```
POST /api/submissions?paper_id=X&sheet_type=omr
          │
          ├── 1. Validate paper_id + sheet_type
          ├── 2. Save image file to uploads/<id>.<ext>
          ├── 3. Insert submission { status:"processing", sheet_type, file_path, ... }
          └── 4. Enqueue evaluate_submission(submission_id) as BackgroundTask
                        │
                        ├── Load submission + paper from MongoDB
                        ├── Call _extract_answers(file_path, sheet_type, mcq_count)
                        │       → OMREngine.process_image()  OR
                        │       → TrOCREngine.extract_text() + parse_mcq_results()
                        ├── Call _grade_mcq(extracted, answer_key, ...)
                        │       → per-question marks supported
                        │       → optional negative marking (−¼ per wrong)
                        ├── Update submission { status:"evaluated", result:{...} }
                        └── Log metrics to MLflow

GET /api/submissions/{id}/status   ← frontend polls every 2 s
          └── Returns { id, status, result }

Frontend auto-redirects to /student/results/{id} when status == "evaluated"
```

---

## Grading Logic

| Condition | Marks |
|-----------|-------|
| Correct answer | `mcqQuestionMarks[Qi]` (per-question) or `mcqMarks` (paper default) |
| Wrong answer, no negative marking | 0 |
| Wrong answer, negative marking on | −¼ × question marks |
| Unanswered | 0 |
| Total below 0 (after negatives) | clamped to 0 |

---

## Student UI Flow (Submission.jsx)

```
/student/submit/:paperId
        │
        ├── Step 1: Choose Sheet Type
        │       ┌─────────────────────────────────┐
        │       │  ⭕ OMR Bubble Sheet             │  OpenCV engine
        │       │  ✍️ Handwritten Answer Sheet     │  TrOCR engine
        │       └─────────────────────────────────┘
        │       [ Continue → ]
        │
        └── Step 2: Upload Image
                • Shows selected type as reminder badge (with "Change" link)
                • Contextual tips for that sheet type
                • UploadZone (JPG / PNG, max 10 MB)
                [ ← Back ]  [ Submit for Evaluation ]
                        │
                        └──► Evaluating screen (⏳ animation, engine name shown)
                                │
                                └──► Auto-redirect to /student/results/:id
```

---

## TrOCR Real vs Stub Mode

TrOCR requires `torch` and `transformers` (~1 GB of model weights from HuggingFace).  
These are **not bundled** to keep the repo lightweight.

| State | Behaviour |
|-------|-----------|
| Both libraries installed, network available | Real inference, `mode = "real"` |
| Libraries installed but no network (offline) | Model load fails → `mode = "stub"` |
| Libraries not installed | Import guard catches it → `mode = "stub"` |

In stub mode submissions still complete but all questions score 0.  
The `result.engine` field reads `trocr_stub` to make this easy to identify.

**To activate real TrOCR:**
```bash
pip install torch transformers
# Model downloads automatically on first inference (~500 MB)
```

---

## File-by-File Purpose

### `backend/app/services/omr_engine.py`
OpenCV bubble-sheet detector.  
Constants `BUBBLE_MIN_W/MAX_W`, `ROW_TOLERANCE`, `MIN_FILL_RATIO` control sensitivity — tune for different DPI or bubble sizes.  
Pass `debug_dir="path/"` to save intermediate threshold + annotated images for inspection.

### `backend/app/services/trocr_engine.py`
Wrapper around Microsoft TrOCR with lazy model loading and graceful stub fallback.  
`extract_text(path)` → `(raw_text, confidence)`.  
`parse_mcq_results(text)` → `{"Q1":"A", ...}` via regex.  
`mode` property: `"real"` | `"stub"` | `"unloaded"`.

### `backend/app/services/evaluator.py`
Async background task triggered after every submission.  
Reads `sheet_type` from the submission, dispatches the correct engine, grades answers, persists results to MongoDB, and logs metrics to MLflow.  
`_extract_answers()` — pure engine dispatch (sync).  
`_grade_mcq()` — pure grading function, no I/O, fully unit-testable.

### `backend/app/routers/submissions.py`
`POST /submissions` now accepts `sheet_type` query param (`"omr"` default) and stores it on the submission document so the background task can read it.

### `frontend/src/pages/student/Submission.jsx`
Two-step wizard: sheet-type selector (Step 1) → file upload (Step 2).  
`SheetTypeCard` — visual option card with icon, description, tips, and engine badge.  
`SHEET_TYPES` constant holds all metadata; add a new entry here to support a third sheet format.

### `frontend/src/hooks/useSubmission.js`
`useSubmitAnswerSheet(paperId, file, sheetType)` — third argument defaults to `"omr"`, appended to the POST as `&sheet_type=...`.

---

## Phase 3 Verification Checklist

| Check | Result |
|-------|--------|
| `OMREngine.process_image()` on synthetic 4-question bubble sheet | ✅ |
| `_grade_mcq()` standard grading: 3/4 correct → score=3.0 | ✅ |
| `_grade_mcq()` negative marking: 2 correct + 2 wrong → score=1.5 | ✅ |
| `_grade_mcq()` per-question marks: Q1=2m + Q2=3m both correct → 5.0 | ✅ |
| `TrOCREngine.parse_mcq_results()` parses "1. A\n2: B\nQ3 C\n4)D" | ✅ |
| TrOCR stub mode activates cleanly when torch is not installed | ✅ |
| `Submission.jsx` Step 1 renders OMR + Handwritten type cards | ✅ |
| `Submission.jsx` Step 2 shows type badge, contextual tips, upload zone | ✅ |
| `useSubmitAnswerSheet` sends `sheet_type` query param | ✅ |
| `POST /submissions?sheet_type=omr` stores field in MongoDB document | ✅ |
| Frontend `npm run build` — zero errors | ✅ |

---

## Self-Verification Commands

Run these from the **repo root** (`/home/m25csa019/Evalify`) to confirm every piece of Phase 3 is working.

---

### 0 — Prerequisites (install once)

```bash
# OpenCV (required for OMR engine)
python3.11 -m pip install opencv-python-headless pillow numpy

# MongoDB async driver + Pydantic settings (required for backend)
python3.11 -m pip install motor==3.4.0 pymongo==4.7.2 pydantic==2.7.1 pydantic-settings==2.2.1

# Optional: real TrOCR inference (~1 GB model download)
# python3.11 -m pip install torch transformers
```

---

### 1 — OMR Engine: synthetic bubble sheet

```bash
cd backend
python3.11 - <<'EOF'
import sys, os, numpy as np, cv2
sys.path.insert(0, ".")
from app.services.omr_engine import OMREngine

# Build a synthetic 4-question bubble sheet (A B C D columns)
img = np.ones((600, 350, 3), dtype=np.uint8) * 255
choices_x = [60, 120, 180, 240]
questions_y = [80, 180, 280, 380]
answers = [0, 2, 1, 3]  # A, C, B, D

for qi, y in enumerate(questions_y):
    for ci, x in enumerate(choices_x):
        cv2.circle(img, (x, y), 18, (0, 0, 0), 2)
        if ci == answers[qi]:
            cv2.circle(img, (x, y), 15, (0, 0, 0), -1)  # filled

path = "/tmp/test_omr.png"
cv2.imwrite(path, img)

omr = OMREngine()
result = omr.process_image(path, mcq_count=4)
print("OMR detected:", result)

expected = {"Q1": "A", "Q2": "C", "Q3": "B", "Q4": "D"}
passed = all(result.get(k) == v for k, v in expected.items())
print("PASS" if passed else f"FAIL — expected {expected}")
EOF
```

**Expected output:**
```
OMR detected: {'Q1': 'A', 'Q2': 'C', 'Q3': 'B', 'Q4': 'D'}
PASS
```

---

### 2 — TrOCR Engine: parser + stub-mode guard

```bash
cd backend
python3.11 - <<'EOF'
import sys; sys.path.insert(0, ".")
from app.services.trocr_engine import TrOCREngine

t = TrOCREngine()

# 2a — parser (works regardless of torch/transformers)
text = "1. A\n2: B\nQ3 C\n4)D"
parsed = t.parse_mcq_results(text)
print("Parser:", parsed)
assert parsed == {"Q1": "A", "Q2": "B", "Q3": "C", "Q4": "D"}, f"FAIL: {parsed}"
print("Parser: PASS")

# 2b — stub / real mode
raw, conf = t.extract_text("/tmp/nonexistent.png")
print(f"Mode: {t.mode}  |  stub sentinel: {raw!r}  |  conf: {conf}")
if t.mode == "stub":
    assert raw == "__TROCR_STUB__" and conf == 0.0
    print("Stub mode: PASS")
else:
    print("Real TrOCR mode active (torch+transformers installed)")

# 2c — parse_mcq_results returns {} in stub mode
answers = t.parse_mcq_results(raw)
print(f"Stub answer map: {answers}  (expected {{}})")
assert answers == {}, f"FAIL: {answers}"
print("Stub answer map: PASS")
EOF
```

**Expected output (no torch/transformers):**
```
Parser: {'Q1': 'A', 'Q2': 'B', 'Q3': 'C', 'Q4': 'D'}
Parser: PASS
Mode: stub  |  stub sentinel: '__TROCR_STUB__'  |  conf: 0.0
Stub mode: PASS
Stub answer map: {}  (expected {})
Stub answer map: PASS
```

---

### 3 — Grading logic: standard + negative + per-question marks

```bash
cd backend
python3.11 - <<'EOF'
import sys; sys.path.insert(0, ".")

# Patch DB imports so evaluator loads without a live MongoDB
import unittest.mock as m
for mod in ("app.db.mongodb", "app.db.mlflow_logger"):
    sys.modules[mod] = m.MagicMock()

from app.services.evaluator import _grade_mcq

key = {"Q1": "A", "Q2": "B", "Q3": "C", "Q4": "D"}

# 3a — all correct
score, correct, _ = _grade_mcq({"Q1":"A","Q2":"B","Q3":"C","Q4":"D"}, key, 4, 1.0, {}, False)
assert score == 4.0 and correct == 4, f"FAIL 3a: {score} {correct}"
print(f"3a all-correct:          score={score}  PASS")

# 3b — 3 correct, 1 wrong, no negative marking
score, correct, _ = _grade_mcq({"Q1":"A","Q2":"B","Q3":"C","Q4":"A"}, key, 4, 1.0, {}, False)
assert score == 3.0 and correct == 3, f"FAIL 3b: {score} {correct}"
print(f"3b 3/4 no-negative:      score={score}  PASS")

# 3c — 2 correct + 2 wrong, negative marking on (−¼ per wrong)
score, correct, _ = _grade_mcq({"Q1":"A","Q2":"B","Q3":"A","Q4":"A"}, key, 4, 1.0, {}, True)
assert score == 1.5, f"FAIL 3c: {score}"
print(f"3c 2+2 negative:         score={score}  PASS")

# 3d — total below 0 after negatives → clamped to 0
score, _, _ = _grade_mcq({"Q1":"B","Q2":"A","Q3":"A","Q4":"B"}, key, 4, 1.0, {}, True)
assert score == 0.0, f"FAIL 3d: {score}"
print(f"3d all-wrong negative:   score={score} (clamped)  PASS")

# 3e — per-question marks: Q1=2m, Q2=3m
score, correct, _ = _grade_mcq({"Q1":"A","Q2":"B"}, {"Q1":"A","Q2":"B"}, 2, 1.0, {"Q1":2.0,"Q2":3.0}, False)
assert score == 5.0, f"FAIL 3e: {score}"
print(f"3e per-question marks:   score={score}  PASS")
EOF
```

**Expected output:**
```
3a all-correct:          score=4.0  PASS
3b 3/4 no-negative:      score=3.0  PASS
3c 2+2 negative:         score=1.5  PASS
3d all-wrong negative:   score=0.0 (clamped)  PASS
3e per-question marks:   score=5.0  PASS
```

---

### 4 — Full-stack smoke test (existing script)

```bash
cd backend
python3.11 -m pytest tests/verify_phase3.py -v
```

Runs the three unittest cases: OMR detection, TrOCR parser, and evaluator coordination with mocked MongoDB.

---

### 5 — Backend import check (no live DB needed)

```bash
cd backend
python3.11 - <<'EOF'
import sys, unittest.mock as m
for mod in ("motor.motor_asyncio", "app.db.mongodb", "app.db.mlflow_logger"):
    sys.modules[mod] = m.MagicMock()

from app.services.omr_engine  import OMREngine
from app.services.trocr_engine import TrOCREngine
from app.services.evaluator   import evaluate_submission, _grade_mcq, _extract_answers
from app.routers.submissions   import router
from app.models.submission     import SubmissionOut, SubmissionStatusOut

print("All Phase 3 modules imported successfully ✓")
print(f"OMREngine constants  — BUBBLE_MIN_W={OMREngine.BUBBLE_MIN_W}  ROW_TOLERANCE={OMREngine.ROW_TOLERANCE}")
print(f"TrOCREngine mode     — {TrOCREngine().mode}")
EOF
```

**Expected output:**
```
All Phase 3 modules imported successfully ✓
OMREngine constants  — BUBBLE_MIN_W=12  ROW_TOLERANCE=15
TrOCREngine mode     — unloaded
```

---

### 6 — Frontend build (zero TypeScript / JSX errors)

```bash
cd frontend
npm run build 2>&1 | tail -10
```

**Expected output (last lines):**
```
✓ built in ...
```
No `error` lines should appear.

---

### 7 — Live API smoke test (server must be running)

Start the backend first:
```bash
cd backend
uvicorn app.main:app --reload --port 47823
```

Then in a second terminal — replace `<TOKEN>` with a valid student JWT:

```bash
# 7a — confirm sheet_type validation rejects bad values
curl -s -X POST "http://localhost:47823/api/submissions?paper_id=000000000000000000000001&sheet_type=bad" \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@/dev/null" | python3 -m json.tool
# Expected: {"detail": "sheet_type must be 'omr' or 'handwritten'."}

# 7b — submit a real OMR sheet (replace paper_id and image path)
curl -s -X POST "http://localhost:47823/api/submissions?paper_id=<PAPER_ID>&sheet_type=omr" \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@/path/to/answer_sheet.png" | python3 -m json.tool
# Expected: submission doc with status="processing", sheet_type="omr"

# 7c — poll until evaluated
curl -s "http://localhost:47823/api/submissions/<SUBMISSION_ID>/status" \
  -H "Authorization: Bearer <TOKEN>" | python3 -m json.tool
# Expected: status="evaluated", result.engine="opencv_omr" (or "trocr_stub")
```

---

### Quick summary of expected pass/fail per check

| # | What it checks | Pass condition |
|---|----------------|----------------|
| 1 | OMR bubble detection | Detects A/C/B/D on synthetic sheet |
| 2 | TrOCR parser + stub mode | Parser maps "1. A\n2: B…" correctly; stub returns sentinel |
| 3 | Grading logic | 5 assertions: standard, no-negative, negative, clamp, per-question |
| 4 | Full unittest suite | `verify_phase3.py` — 3 tests green |
| 5 | Module imports | All Phase 3 symbols importable without a running DB |
| 6 | Frontend build | Zero errors, bundles cleanly |
| 7 | Live API | `sheet_type` validation + submission + status poll |

---

## Manual End-to-End Walkthrough

Run these **server start commands first**, then follow the step-by-step UI walkthrough below.

---

### Step 0 — Start all three servers

Open **three separate terminal tabs/windows** and run one command per tab.

**Tab 1 — MongoDB + MLflow (Docker)**
```bash
cd /home/m25csa019/Evalify
docker compose -f docker-compose.dev.yml up -d
# Verify containers are healthy:
docker compose -f docker-compose.dev.yml ps
```
MongoDB will be available on `localhost:27017`.  
MLflow UI will be available on `http://localhost:5005`.

**Tab 2 — FastAPI Backend**
```bash
cd /home/m25csa019/Evalify/backend
python3.11 -m uvicorn app.main:app --reload --port 47823
```
Wait until you see:
```
INFO:     Application startup complete.
```
Seed output will also print:
```
🌱 Seeded teacher: teacher@evalify.local
🌱 Seeded student: CS2025001
```
Backend API is at `http://localhost:47823`.  
API docs (Swagger) at `http://localhost:47823/docs`.

**Tab 3 — React Frontend (Vite dev server)**
```bash
cd /home/m25csa019/Evalify/frontend
npm run dev
```
Wait until you see:
```
  ➜  Local:   http://localhost:5173/
```
Open `http://localhost:5173` in your browser.

---

### Step 1 — Teacher: Create an MCQ Paper

**Login credentials (seeded by backend on first start):**
- URL: `http://localhost:5173/teacher/login`
- Email: `teacher@evalify.local`
- Password: `Teacher@123`

**Actions in the UI:**
1. After login you land on the **Teacher Dashboard**.
2. Click **"Create New Paper"** (or the `+` button).
3. Fill in the paper details:
   - **Name**: e.g. `CS101 Mid-Term`
   - **Type**: select **MCQ**
   - **Total Marks**: e.g. `20`
   - **MCQ Count**: e.g. `4`
   - **Marks per question**: e.g. `5`
   - **Negative Marking**: toggle on/off as desired
4. In the **Answer Key** section, fill in correct answers:
   - Q1: `A`, Q2: `B`, Q3: `C`, Q4: `D`
5. Click **"Create Paper"** / **"Save"**.

**What to verify:**
- Paper appears in the dashboard paper list.
- Paper `type` is shown as `MCQ`.
- Answer key is stored (visible if you open the paper).

---

### Step 2 — Teacher: Verify the Paper Exists in the Backend

In the browser address bar open the Swagger UI to confirm:
```
http://localhost:47823/docs
```
Or use curl to list papers (no auth needed for the docs):
```bash
# Get teacher JWT first
curl -s -X POST http://localhost:47823/api/auth/teacher/login \
  -H "Content-Type: application/json" \
  -d '{"email":"teacher@evalify.local","password":"Teacher@123"}' \
  | python3 -m json.tool
# Copy the "access_token" value

# List all papers
curl -s http://localhost:47823/api/papers \
  -H "Authorization: Bearer <TEACHER_TOKEN>" \
  | python3 -m json.tool
```
**What to verify:**
- The paper you created appears in the list.
- `"type": "mcq"` is present.
- `"mcqAnswers": {"Q1":"A","Q2":"B","Q3":"C","Q4":"D"}` is present.
- Copy the `"id"` field — you'll need it for the student submission step.

---

### Step 3 — Student: Login

**Login credentials:**
- URL: `http://localhost:5173/student/login`
- Roll No: `CS2025001`
- Password: `Student@123`

After login you land on the **Student Dashboard**.  
The paper `CS101 Mid-Term` should appear in the **Available Papers** list.

---

### Step 4A — Student: Submit via OMR Bubble Sheet

**Prerequisite — prepare a test OMR image:**

Run this in the backend directory to generate a synthetic bubble sheet image:
```bash
cd /home/m25csa019/Evalify/backend
python3.11 - <<'EOF'
import numpy as np, cv2

img = np.ones((600, 350, 3), dtype=np.uint8) * 255
choices_x = [60, 120, 180, 240]   # A B C D columns
questions_y = [80, 180, 280, 380]  # Q1 Q2 Q3 Q4 rows
# Fill Q1:A, Q2:B, Q3:C, Q4:D
filled = [0, 1, 2, 3]

for qi, y in enumerate(questions_y):
    for ci, x in enumerate(choices_x):
        cv2.circle(img, (x, y), 18, (0, 0, 0), 2)         # bubble outline
        if ci == filled[qi]:
            cv2.circle(img, (x, y), 15, (0, 0, 0), -1)    # filled bubble

cv2.imwrite("/tmp/student_omr_sheet.png", img)
print("Saved: /tmp/student_omr_sheet.png")
EOF
```

**Actions in the Student UI:**
1. Click **"Submit Answer Sheet"** next to `CS101 Mid-Term`.
2. **Step 1 — Choose Sheet Type**:
   - You see two cards: **OMR Bubble Sheet** (OpenCV) and **Handwritten Answer Sheet** (TrOCR).
   - Select **OMR Bubble Sheet** (the `⭕` card).
   - Click **"Continue with OMR Bubble Sheet →"**.
3. **Step 2 — Upload Image**:
   - The reminder badge at the top shows `⭕ OMR Bubble Sheet — Engine: OpenCV OMR`.
   - Drag and drop or click to upload `/tmp/student_omr_sheet.png`.
   - Click **"Submit for Evaluation"**.
4. The **Evaluating screen** appears:
   - Shows `⏳` animation.
   - Text reads: `"Detecting filled bubbles with computer vision…"`.
   - `Engine: OpenCV OMR` is shown.
5. After ~2–5 seconds the page **auto-redirects** to `/student/results/<id>`.

**What to verify on the Results page:**
- Status: `evaluated`
- Score is shown (should be `20/20` if all 4 answers match A/B/C/D).
- Each question shows correct/incorrect.
- `result.engine` in the backend = `opencv_omr`.

**Verify via curl:**
```bash
# Get student JWT
curl -s -X POST http://localhost:47823/api/auth/student/login \
  -H "Content-Type: application/json" \
  -d '{"roll_no":"CS2025001","password":"Student@123"}' \
  | python3 -m json.tool
# Copy "access_token"

# Check submission status (replace SUBMISSION_ID from URL bar)
curl -s http://localhost:47823/api/submissions/<SUBMISSION_ID>/status \
  -H "Authorization: Bearer <STUDENT_TOKEN>" \
  | python3 -m json.tool
```
Expected response:
```json
{
  "id": "<SUBMISSION_ID>",
  "status": "evaluated",
  "result": {
    "score": 20.0,
    "engine": "opencv_omr",
    "correct": 4,
    "total": 4
  }
}
```

---

### Step 4B — Student: Submit via Handwritten Answer Sheet (TrOCR)

**Prerequisite — prepare a handwritten-style text image:**

```bash
python3.11 - <<'EOF'
from PIL import Image, ImageDraw, ImageFont
import os

img = Image.new("RGB", (400, 200), "white")
draw = ImageDraw.Draw(img)
text = "1. A\n2. B\n3. C\n4. D"
draw.text((20, 20), text, fill="black")
img.save("/tmp/student_handwritten.png")
print("Saved: /tmp/student_handwritten.png")
EOF
```

**Actions in the Student UI:**
1. From the dashboard, click **"Submit Answer Sheet"** again (or go back).
2. **Step 1 — Choose Sheet Type**:
   - Select **Handwritten Answer Sheet** (the `✍️` card).
   - Click **"Continue with Handwritten Answer Sheet →"**.
3. **Step 2 — Upload Image**:
   - The reminder badge shows `✍️ Handwritten Answer Sheet — Engine: TrOCR (Handwriting OCR)`.
   - Upload `/tmp/student_handwritten.png`.
   - Click **"Submit for Evaluation"**.
4. The **Evaluating screen** text reads: `"Reading your handwriting with TrOCR…"`.
5. After evaluation, results appear.

**What to verify:**
- If `torch` + `transformers` are **not** installed (default):
  - `result.engine` = `trocr_stub`
  - Score = `0` (stub mode returns no answers — expected behaviour).
  - The submission still **completes** without crashing.
- If real TrOCR is installed (`pip install torch transformers`):
  - `result.engine` = `trocr_real`
  - Answers parsed from the image text via OCR.

**Verify via curl:**
```bash
curl -s http://localhost:47823/api/submissions/<SUBMISSION_ID>/status \
  -H "Authorization: Bearer <STUDENT_TOKEN>" \
  | python3 -m json.tool
```
Expected (stub mode):
```json
{
  "status": "evaluated",
  "result": {
    "score": 0.0,
    "engine": "trocr_stub",
    "note": "TrOCR running in stub mode — install torch + transformers for real inference"
  }
}
```

---

### Step 5 — Teacher: View Submission Results

1. Login as teacher: `http://localhost:5173/teacher/login`.
2. Go to **Dashboard** → click the paper `CS101 Mid-Term`.
3. Click **"View Results"** (or navigate to `/teacher/results/<paper_id>`).
4. You should see a results table with:
   - Student name: `Aarav Sharma`
   - Roll No: `CS2025001`
   - Score for the OMR submission.
   - Score for the handwritten/stub submission (if both submitted).

---

### Step 6 — Verify MLflow Logs

Open the MLflow UI:
```
http://localhost:5005
```
- Each evaluation run is logged as a separate MLflow **run** under experiment `evalify_submissions`.
- Logged **metrics**: `score`, `accuracy`, `latency_s`, `ocr_confidence`.
- Logged **params**: `engine`, `sheet_type`, `trocr_mode`, `paper_id`, `roll_no`.

---

### Summary: What "Working Correctly" Looks Like

| Scenario | Expected Result |
|----------|----------------|
| Teacher creates MCQ paper with answer key | Paper saved, answers stored in MongoDB |
| Student selects OMR, uploads bubble image | Engine shown as `OpenCV OMR`, status reaches `evaluated` |
| OMR score with matching answers | `20/20` (or proportional) |
| Student selects Handwritten | Engine shown as `TrOCR (Handwriting OCR)` |
| TrOCR stub mode (no torch) | Status `evaluated`, score=0, engine=`trocr_stub`, no crash |
| TrOCR real mode (torch installed) | OCR text extracted, answers parsed, score calculated |
| Wrong `sheet_type` via API | HTTP 400 with descriptive error message |
| MLflow UI | One run per evaluation with metrics + params |

---

## Phase Checklist

| Phase | Status |
|-------|--------|
| Phase 0 | ✅ Done |
| Phase 1 | ✅ Done |
| Phase 2 | ✅ Done |
| **Phase 3** | ✅ Done |
| Phase 4 | Type 2 — MCQ + Numerical (tolerance grading) |
| Phase 5 | Type 3 — Subjective + LLM + MLflow |
| Phase 6 | Docker containerisation |
| Phase 7 | Kubernetes deployment |
| Phase 8 | Production deploy |
