# Evalify manual test checklist

Tick each box as you go. Each item says what to do and, after the arrow, what you should see. Write anything that
looks wrong in the "Notes" line at the end of the section, with the account and paper you used.

Accounts (all from `demo.env`):

| Role | Login | Password |
|---|---|---|
| Teacher (Physics, has the dummy data) | `physics.teacher@evalify.local` | `Teacher@123` |
| Teacher (Computer Science) | `teacher@evalify.local` | `Teacher@123` |
| TA (Physics) | `ta.physics@evalify.local` | `Ta@12345` |
| TA (Physics and Mathematics) | `ta.science@evalify.local` | `Ta@12345` |
| Student (Physics, dummy sheets on all five papers) | `PH2025001` | `Student@123` |
| Student (Physics, no dummy sheet) | `PH2025020` | `Student@123` |
| Student (Computer Science only) | `CS2025010` | `Student@123` |

Date of this run: ______________  Branch / commit: ______________

---

## 0. Before you start

- [ ] MongoDB is running → `bash infra/cluster/mongo.sh status` says "running"
- [ ] Backend is up → `http://localhost:47823/api/health` returns `"status":"ok"`
- [ ] API docs load → `http://localhost:47823/docs` lists the auth, papers, submissions, results, ta and evaluation endpoints
- [ ] Frontend is up → `http://localhost:5173` shows the login page
- [ ] Dummy data is loaded → `python -m app.db.demo_data` (from `backend/`) prints 5 papers and 45 submissions
- [ ] GPU job status known → `squeue -u $USER` (needed only for sections 5 and 10 with handwritten sheets)
- [ ] If the GPU job is running, the backend reads the same endpoints file the job writes (`EVALIFY_ENDPOINTS_FILE`)
- [ ] Automated tests pass first → `pytest tests/ -q` in `backend/` and `npm test` in `frontend/`

Notes:

---

## 1. Login and navigation

- [ ] Teacher login with correct password → teacher home page
- [ ] Teacher login with wrong password → error message, stays on the login page
- [ ] Student login with roll number → student home page
- [ ] Student login with wrong roll number → error message
- [ ] TA login → TA home page
- [ ] While logged in as a teacher, open `/student/dashboard` → sent to the student login, not shown student data
- [ ] While logged in as a student, open `/teacher/dashboard` → sent to the teacher login
- [ ] While logged in, open a login page → sent to your own home page
- [ ] Unknown URL (for example `/abc`) → "not found" page with a way back
- [ ] Logout from the navbar → back to the login page; the browser Back button does not show the old page's data
- [ ] Refresh the page while logged in → still logged in
- [ ] Links between the three login pages (teacher, student, TA) work

Notes:

---

## 2. Teacher home page

- [ ] Header shows "Teacher / Dr. Meera Iyer" and "Subject: Physics"
- [ ] Header for `teacher@evalify.local` shows "Subject: Computer Science"
- [ ] "My papers" lists the five dummy Physics papers with question count and released / not released state
- [ ] A teacher with no papers sees "No papers yet. Use "Create paper" to add your first exam."
- [ ] "View Paper" opens the paper page; "View Results" opens the results page
- [ ] A teacher sees only their own papers (log in as the Computer Science teacher: no Physics papers)

Notes:

---

## 3. Creating a paper (wizard)

Steps: Paper Type, Details, Answer Key, Configuration, Review. Do this once for each paper type.

### 3a. Type A, MCQ only

- [ ] Step 1: choose "MCQ Only" → Next is enabled only after choosing
- [ ] Step 2: name, subject, number of MCQ questions, question paper PDF upload → the PDF uploads and shows its name
- [ ] Step 2: required fields left empty → Next is blocked with a message
- [ ] Step 3: answer key from the uploaded key PDF → the MCQ answers are filled in
- [ ] Step 3: answer key typed by hand → saved
- [ ] Step 3: "Multiple accepted answers" for one question (for example A,C) → kept
- [ ] Step 4: negative marking on, marks deducted per wrong answer → value kept
- [ ] Step 4: OMR blank template sheet uploaded (if offered) → accepted
- [ ] Step 5: review shows everything entered → "Create paper" creates it and shows the success message
- [ ] Back button between steps keeps what was entered

### 3b. Type B, MCQ + numerical

- [ ] Numerical answer key with a tolerance → saved
- [ ] Numbering choice (MCQ section first, or numbering as on the paper) → shown correctly on the review step
- [ ] Total marks on the review step = MCQ marks + numerical marks

### 3c. Type C, MCQ + numerical + written answers

- [ ] Grade rubric PDF and detailed answer PDF uploaded → "Rubric Setup" shows key concepts and marks per concept per question
- [ ] A question with no concepts shows "No concepts extracted for this question." and can be filled by hand
- [ ] Mandatory concept can be marked
- [ ] Marks per question can be set ("Custom per question")
- [ ] Answer-key assistant: "Draft the answer key from your notes", add reference files (PDF with text or .txt), click "Draft answer key" → a draft reference answer per written question (needs the GPU models)
- [ ] Answer-key assistant without models running → a clear error, the wizard still works
- [ ] Draft answer can be edited before saving

### 3d. After creating

- [ ] The new paper appears on the teacher home page
- [ ] Students of that subject see it (log in as `PH2025020` for a Physics paper)
- [ ] Students of another subject do not see it (log in as `CS2025010`)
- [ ] Delete a test paper (if the UI offers it, or `DELETE /api/papers/{id}` in the API docs) → gone from both teacher and student lists

Notes:

---

## 4. Paper page (teacher)

- [ ] "Marks overview": MCQ, numerical and written question counts and total marks are right
- [ ] MCQ answer key and numerical answers shown match what was entered
- [ ] Written questions show key concepts and mandatory concepts
- [ ] "Uploaded documents": question paper, answer key, answer sheet and rubric PDFs open
- [ ] "View Results" and "Back to Dashboard" work
- [ ] Another teacher's paper ID in the URL → "Paper not found"

Notes:

---

## 5. Student upload

Use `PH2025020` (no dummy sheet) on a Physics paper, and the photos in `uploads/`.

- [ ] Student home shows the enrolled subjects; a subject page lists its papers with a status badge
- [ ] Open a paper → "Upload Answer Sheet" page with the tips for the sheet type
- [ ] Handwritten-only paper shows "This paper requires a handwritten answer sheet."
- [ ] Choose OMR or handwritten sheet type (where both are allowed)
- [ ] Add one page by drag and drop, and one by click → both shown, in order
- [ ] "Add another page" for a two-page sheet → order kept
- [ ] Remove a page before uploading → removed
- [ ] Wrong file type (PDF or .txt) → refused with a message
- [ ] File over 10 MB → refused with a message
- [ ] Upload → message that the sheet is submitted and will be evaluated when the teacher starts the evaluation
- [ ] Subject page now shows the badge "Submitted" and a disabled "Waiting for evaluation" button
- [ ] Nothing is evaluated yet: the teacher's results page counts the sheet as waiting
- [ ] Upload again for the same paper → refused, or replaces the earlier sheet (write down which)
- [ ] A Computer Science student cannot upload to a Physics paper (try the URL `/student/submit/<physics paper id>`)

Notes:

---

## 6. Start evaluation (teacher)

Dummy data: "MCQ Basic Science" has 3 sheets waiting, paper 2B has 1.

- [ ] Results page shows the "Evaluation" panel above the release panel
- [ ] Panel says "3 answer sheets waiting for evaluation." (the right count for the paper)
- [ ] A paper with nothing waiting says "No answer sheets are waiting for evaluation." and the button is disabled
- [ ] Click "Start evaluation" → "Stage 1 of 2: Reading answer sheets" with a count such as 0 / 3
- [ ] The button is disabled while the batch runs
- [ ] Counts go up without refreshing the page (every 5 seconds)
- [ ] Stage changes to "Stage 2 of 2: Grading answers" only after every sheet is read
- [ ] At the end: "Evaluation finished" with date and time, and the results table refreshes by itself
- [ ] Marks of each evaluated sheet match the gold labels in `eval/data/own_*/manifest.jsonl`
- [ ] Students still see "Submitted" or "being evaluated" during the batch, never partial marks
- [ ] Upload a new sheet while a batch runs → it is not added to the running batch; it waits for the next click
- [ ] A sheet that cannot be read (blurred or blank photo) → "1 sheet could not be evaluated; it is included again when you start evaluation."
- [ ] Clicking "Start evaluation" again picks up the failed sheet
- [ ] Restart the backend during stage 1 (`bash infra/cluster/app.sh stop`, then `start`) → the batch continues by itself, no sheet lost or marked twice
- [ ] Without model servers: OMR sheets are still marked; handwritten sheets end as failed with a reason
- [ ] Only the paper's teacher can start it (another teacher gets "not found" on that paper)

Notes:

---

## 7. Results page (teacher)

- [ ] Summary: number of submissions, average and percentage look right
- [ ] Table shows each student's name, roll number, status and marks
- [ ] Status badges are right: "TA pending", "TA reviewed", "Re-evaluation pending", "Re-evaluated", "Hand-marked"
- [ ] Open one sheet → the photo(s) and the question-wise marks; "How this answer was marked" explains the marks
- [ ] Written answers show the transcript, concepts found and concepts missing
- [ ] Hand-mark: change one question's mark → total updates, sheet shows "Hand-marked", the change appears in the marks history
- [ ] Hand-mark with a mark above the maximum or below 0 → refused
- [ ] Calibration ("Match your marking style (optional)"): hand-mark a few sheets, "Apply calibration" → written marks shift, "calibration active" shown
- [ ] "Remove calibration" → marks go back to the rubric marks

Notes:

---

## 8. TA

Log in as `ta.physics@evalify.local`.

- [ ] TA home lists the TA's subjects and "Answer sheets to review"
- [ ] "Flagged by AI" tab lists the flagged dummy sheets, each with a reason
- [ ] "Re-evaluation requests" tab lists the pending requests with the student's remark
- [ ] An empty tab says "Nothing to review in this tab."
- [ ] Open a flagged item → photo, what the models read, the AI mark, the answer key, and reference PDFs (question paper, answer key, rubric, reference solution)
- [ ] Change one mark and add a remark → submit → the item leaves the queue
- [ ] Leave all marks unchanged and submit → the AI marks are kept and the item leaves the queue
- [ ] The teacher's results page then shows "TA reviewed" and the new total
- [ ] Answer a re-evaluation request → the student sees "Re-evaluated by a TA", the new marks and the remark
- [ ] `ta.science@evalify.local` sees both Physics and Mathematics items
- [ ] A TA with no subject sees "You are not a TA of any subject yet."
- [ ] A TA cannot open a sheet of a subject they don't cover (change the ID in `/ta/review/<id>`)

Notes:

---

## 9. Releasing marks

- [ ] Unreleased paper: panel says "Not released to students" and "Students see "Your answer sheet is being evaluated" until you release."
- [ ] Student of an unreleased paper sees "Your answer sheet is being evaluated", no marks
- [ ] "Release results" → message "Results released to students.", panel says "Released to students"
- [ ] Release while TA items are still open → warning about sheets with open TA work
- [ ] Student now sees the marks
- [ ] "Withdraw release" → students no longer see the marks

Notes:

---

## 10. Student results and re-evaluation

Log in as `PH2025001`.

- [ ] Released papers show "View Result"; unreleased papers do not show marks
- [ ] Result page: "Your score", "Percentage", "Class average", "Section Breakdown" (MCQ, numerical, written), "Question-wise marks"
- [ ] The uploaded photos open on the result page
- [ ] Ask for re-evaluation with a remark → "Re-evaluation requested — waiting for a TA"
- [ ] A second re-evaluation request on the same paper is not possible ("You can ask only once for this paper.")
- [ ] After the TA answers → "Re-evaluated by a TA", new marks, and the "Marks history" lists the old and new marks
- [ ] Another student's result URL (`/student/results/<other id>`) → refused

Notes:

---

## 11. Look and feel

- [ ] No emoji anywhere in the app
- [ ] The "marked paper" style is used throughout: paper colours, ruled lines, pen-coloured marks
- [ ] Each page works at phone width (browser dev tools, 375 px): no sideways scrolling, buttons reachable
- [ ] Loading states show skeletons or "Loading...", not a blank page
- [ ] Error and success messages (toasts) appear and disappear
- [ ] Long names and long paper titles do not break the layout
- [ ] Keyboard only: Tab through the login form and the upload page; Enter submits

Notes:

---

## 12. Security and data

- [ ] API without a token (`GET /api/papers` in the API docs without logging in) → 401
- [ ] Student token on a teacher endpoint (`POST /api/papers/{id}/evaluate`) → 403
- [ ] Page photos of one student cannot be opened by another student (`/api/submissions/{id}/pages/0`)
- [ ] `git status` shows no `.env` files with secrets, no `mongo.env`, no uploaded photos outside `backend/uploads/demo/`
- [ ] JWT secrets are not the default placeholders on any shared machine (see the Configuration reference in README.md)
- [ ] `python -m app.db.demo_data --clear` removes only the dummy data; papers you created in this run remain

Notes:

---

## 13. Models and GPU job (only when the models are needed)

- [ ] `squeue -u $USER` shows the job RUNNING on cn07
- [ ] The endpoints file lists Gemma, Qwen and GLM-OCR with their ports
- [ ] `curl http://cn07:<port>/v1/models` answers for each model
- [ ] Server logs (`/scratch/$USER/evalify/logs/`) show no errors after start-up
- [ ] One handwritten sheet evaluated end to end with marks close to the gold labels
- [ ] When finished: release the GPUs (`scancel <job id>`) so others can use cn07

Notes:

---

## Summary

| Section | Passed | Failed | Not tested |
|---|---|---|---|
| 0 Before you start | | | |
| 1 Login and navigation | | | |
| 2 Teacher home page | | | |
| 3 Creating a paper | | | |
| 4 Paper page | | | |
| 5 Student upload | | | |
| 6 Start evaluation | | | |
| 7 Results page | | | |
| 8 TA | | | |
| 9 Releasing marks | | | |
| 10 Student results and re-evaluation | | | |
| 11 Look and feel | | | |
| 12 Security and data | | | |
| 13 Models and GPU job | | | |

Problems found:

1.
2.
3.
