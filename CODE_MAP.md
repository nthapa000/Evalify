# Evalify code map: how the system works and where every feature lives

Written 17 Nov 2026 (branch `pipeline-v2`). For anyone who needs to find, change or test a feature. Setup is in
[README.md](README.md); design and diagrams are in [Architecture Diagram/](Architecture%20Diagram/).

Contents

1. The system in one page
2. Directory tree
3. The end-to-end flow, step by step, with the files involved
4. Feature map: every feature, its screen, its API and its code
5. The marking pipeline, file by file
6. Data: MongoDB collections and files on disk
7. Model serving and cluster scripts
8. Evaluation harness and reports
9. Tests
10. Documents
11. Where to change things

---

## 1. The system in one page

```
Browser (React, frontend/)  ──/api──►  FastAPI backend (backend/app/)  ──►  MongoDB (users, papers, submissions, batches)
                                              │                        ──►  backend/uploads/ (photos, PDFs)
                                              ▼
                                  Marking pipeline (backend/app/pipeline/)
                                              │  OpenAI-compatible HTTP
                                              ▼
                     vLLM model servers on the GPU node (infra/): Gemma x2, Qwen, GLM-OCR
```

Roles: **teacher** (creates papers, starts evaluation, releases marks), **TA** (checks flagged answers and
re-evaluation requests), **student** (uploads sheets, sees released marks). Users come from `demo.env`.

Paper types: **A** MCQ only (OMR bubble sheet or handwritten), **B** MCQ + numerical, **C** MCQ + numerical +
written answers.

---

## 2. Directory tree

```
Evalify/
├── backend/                     FastAPI application, marking pipeline, tests
│   ├── app/
│   │   ├── main.py              app start-up: routers, CORS, MongoDB, demo users, batch recovery
│   │   ├── config.py            settings from environment variables
│   │   ├── routers/             HTTP endpoints (all under /api)
│   │   ├── services/            application logic used by the routers
│   │   ├── pipeline/            marking pipeline: quality gate, readers, OMR, scoring, grader, routing
│   │   ├── prompts/             prompts and JSON schemas sent to the models
│   │   ├── models/              request/response schemas (Pydantic)
│   │   └── db/                  MongoDB access, demo users, dummy data, MLflow logging
│   ├── tests/                   pytest suite (in-memory DB, models stubbed)
│   ├── uploads/                 stored photos (uploads/) and paper PDFs (uploads/papers/)
│   ├── db/mongo-init.js         Docker MongoDB init
│   ├── requirements.txt         Python packages
│   └── Dockerfile, start.sh, Ollama.md   older Ollama-based set-up
├── frontend/                    React + Vite web app
│   ├── src/                     pages, components, hooks, stores, utils, tests
│   ├── vite.config.js           dev server 5173, /api proxied to 47823
│   └── tailwind.config.js       "marked paper" colours and fonts
├── infra/
│   ├── models.yaml              every model, serving profiles, roles (single source of truth)
│   └── cluster/                 Slurm jobs, vLLM launcher, MongoDB and app scripts
├── eval/                        evaluation harness, labelled data, experiment scripts, reports
├── uploads/                     upload kit for manual testing (Pattern1/2/3)
├── Architecture Diagram/        high level design, Mermaid diagrams, sequence diagrams, JPGs
├── testing_data/                sample MCQ question paper and key
├── k8s/                         Kubernetes namespace (not used yet)
├── .github/workflows/           CI: backend tests, frontend build and lint, Docker build
├── demo.env                     demo users (teachers, TAs, students)
├── docker-compose.dev.yml       local MongoDB + MLflow (Docker)
└── *.md                         plans, decisions, experiments (section 10)
```

---

## 3. The end-to-end flow, step by step

| Step | Who | What happens | Screen (frontend/src) | API | Backend code |
|---|---|---|---|---|---|
| 1 | Anyone | Signs in, gets a JWT | `pages/auth/*Login.jsx`, `hooks/useAuth.js`, `store/authStore.js` | `POST /api/auth/{teacher,student,ta}/login` | `routers/auth.py`, `db/seed.py`, `db/demo_users.py` |
| 2 | Teacher | Creates a paper in the 5-step wizard | `pages/teacher/CreatePaper.jsx` + `components/forms/*` | `POST /api/papers`, file uploads, extraction endpoints | `routers/papers.py`, `services/pdf_utils.py`, `services/rubric_extractor.py`, `pipeline/omr_template.py`, `services/answer_key.py` |
| 3 | Student | Uploads photos of the answer sheet (stored, not marked) | `pages/student/Submission.jsx`, `hooks/useSubmission.js` | `POST /api/submissions?paper_id=&sheet_type=` | `routers/submissions.py` |
| 4 | Teacher | Clicks "Start evaluation" | `components/results/EvaluationPanel.jsx` on `pages/teacher/PaperResults.jsx` | `POST /api/papers/{id}/evaluate`, `GET /api/papers/{id}/evaluation` | `routers/evaluation.py`, `services/batch_runner.py` |
| 5 | System | Stage 1: reads every sheet | (progress in EvaluationPanel) | none | `services/evaluator.read_submission` → `pipeline/orchestrator.read_sheet` |
| 6 | System | Stage 2: grades every sheet, flags doubtful answers | (progress) | none | `services/evaluator.evaluate_submission` → `pipeline/orchestrator.grade_sheet` |
| 7 | TA | Checks flagged answers, sets final marks | `pages/ta/Dashboard.jsx`, `pages/ta/Review.jsx`, `hooks/useTa.js` | `GET /api/ta/subjects`, `GET /api/ta/queue`, `GET /api/ta/items/{id}`, `POST /api/ta/items/{id}/marks` | `routers/ta.py`, `services/marks.py`, `services/access.py` |
| 8 | Teacher | Reviews results, hand-marks, calibrates, releases | `pages/teacher/PaperResults.jsx` | `GET /api/results/paper/{id}`, `PUT /api/papers/{id}/release`, calibration endpoints | `routers/results.py`, `routers/papers.py`, `routers/calibration.py`, `pipeline/calibration.py` |
| 9 | Student | Sees marks, may ask once for re-evaluation | `pages/student/Result.jsx`, `components/results/MarkBreakdown.jsx`, `EvaluationNotice.jsx` | `GET /api/results/{id}`, `POST /api/submissions/{id}/reevaluation` | `routers/results.py`, `routers/submissions.py`, `services/access.py` |
| 10 | TA | Answers the re-evaluation request | `pages/ta/Review.jsx` (tab "Re-evaluation requests") | `POST /api/ta/items/{id}/marks` | `routers/ta.py`, `services/marks.py` |

---

## 4. Feature map

Each feature: what it does, the screen, the endpoint(s), the backend code and its tests.

### 4.1 Login and users
- Three logins (teacher and TA by email, student by roll number), JWT per role (expiry 8 h / 4 h), bcrypt.
- Users and enrolments come from `demo.env`, created or updated at every start-up. Teachers may have two
  subjects (`Physics;Mathematics`), TAs several, students several.
- Frontend: `pages/auth/TeacherLogin.jsx`, `StudentLogin.jsx`, `TaLogin.jsx`, `components/layout/AuthShell.jsx`,
  `hooks/useAuth.js`, `store/authStore.js`, `utils/validators.js`; route guards in `App.jsx`.
- Backend: `routers/auth.py` (login, `get_current_user`, `require_teacher` / `require_student` / `require_ta`,
  `user_subjects`), `db/demo_users.py` (parses `demo.env`), `db/seed.py` (creates users), `config.py` (secrets).
- Tests: `backend/tests/test_auth.py`, `test_demo_users.py`; `frontend/src/pages/auth/__tests__/`, `store/__tests__/`.

### 4.2 Teacher home page
- Lists the teacher's papers, shows name and subject(s) in the header.
- Frontend: `pages/teacher/Dashboard.jsx`, `hooks/usePapers.js` (`useTeacherPapers`).
- Backend: `GET /api/papers` in `routers/papers.py`.

### 4.3 Creating a paper (5-step wizard)
Frontend: `pages/teacher/CreatePaper.jsx` (Step1 to Step5, `canNext`, `handleSubmit`), `components/forms/StepWizard.jsx`.

| Part of the wizard | Frontend | Endpoint | Backend |
|---|---|---|---|
| Paper type (A / B / C) | `CreatePaper.jsx` Step1 | none | none |
| Subject (fixed, or choice for a two-subject teacher) | `components/forms/SubjectField.jsx` | none | subject check in `routers/papers.py create_paper` |
| Question paper PDF upload | `PdfUploadZone` in `CreatePaper.jsx` | `POST /api/papers/files/upload` | `routers/papers.py upload_paper_file` (files in `backend/uploads/papers/`) |
| Count questions in the PDF | `handleQuestionPaper` in Step2, `detectQuestionCount` in `hooks/usePapers.js` | `POST /api/papers/detect-questions` | `services/pdf_utils.count_questions` |
| OMR or handwritten (MCQ-only papers) | `components/forms/AnswerSheetFormat.jsx` | stored as `answerSheetFormat` | enforced in `routers/submissions.py` |
| Marks per question, negative marking, numbering S1 or Q21 | Step2 / Step4, `components/forms/NumberingChoice.jsx` | none | used by `pipeline/readers.questions_for` and `pipeline/scoring.py` |
| MCQ key from a PDF | Step3 | `POST /api/papers/extract-answers` | `services/pdf_utils.extract_mcq_answers_from_pdf`, `parse_mcq_text` |
| Blank OMR sheet (required for OMR) | `OmrTemplateCard` in `CreatePaper.jsx`, `omrTemplateIncomplete` in `utils/validators.js` | `POST /api/papers/omr-template` | `pipeline/omr_template.build_template`, `preview`; server check in `create_paper` |
| Rubrics from two PDFs (type C) | Step4, `components/forms/RubricBuilder.jsx` | `POST /api/papers/extract-rubric` | `services/rubric_extractor.py` |
| Answer-key assistant (RAG, type C only) | `components/forms/AnswerKeyAssistant.jsx` | `POST /api/papers/answer-key/draft` | `services/answer_key.py`, `prompts/prompt_pipeline.answer_key_prompt` |
| Review and create | Step5 | `POST /api/papers` | `routers/papers.py create_paper`, `models/paper.py` |

Tests: `backend/tests/test_papers.py`, `test_answer_key_pdf.py`, `test_answer_key.py`, `test_omr_template.py`;
`frontend/src/pages/teacher/__tests__/pages.test.jsx`, `components/forms/__tests__/`.

### 4.4 Paper page (teacher)
- Marks overview, MCQ key (multi-answer keys highlighted), numerical key, written questions and rubric, all uploaded
  documents (question paper, answer key, detailed solution, detailed answers, grading rubric, OMR layout).
- Frontend: `pages/teacher/PaperView.jsx`. Backend: `GET /api/papers/{id}`, `GET /api/papers/files/{name}`.

### 4.5 Student upload
- Subject list, paper list with status, upload of page photos (PNG/JPG, 10 MB each, page order kept); only the sheet
  type the teacher chose is offered; the sheet waits with status "submitted".
- Frontend: `pages/student/Dashboard.jsx`, `SubjectPage.jsx`, `Submission.jsx`, `hooks/useSubmission.js`.
- Backend: `GET /api/papers/available` (`routers/papers.py`), `POST /api/submissions` (`routers/submissions.py`:
  file checks, enrolment, `answerSheetFormat`), page images `GET /api/submissions/{id}/pages/{i}`.
- Tests: `test_submissions.py`, `frontend/src/pages/student/__tests__/`.

### 4.6 Start evaluation (batch)
- One click queues every waiting sheet; stage 1 reads all, stage 2 grades all, 32 sheets at a time; progress,
  elapsed time, slow and failed states on the page; survives backend restarts; a crashed batch's sheets can be
  sent again.
- Frontend: `components/results/EvaluationPanel.jsx` (polls every 5 s).
- Backend: `routers/evaluation.py`; `services/batch_runner.py` (`start`, `run_batch`, `_stage`, `recover`,
  `_guarded`, optional `stage_hook` model swap); `services/evaluator.py` (`read_submission`, `evaluate_submission`,
  MLflow logging in a worker thread); restart recovery called from `main.py`.
- Tests: `test_batch_evaluation.py`, `test_evaluator.py`, `test_mlflow_logger.py`, `EvaluationPanel.test.jsx`.

### 4.7 Results, hand-marking, calibration, release (teacher)
- Results table, sheet photos, per-question marks and reasons; hand-marking with history; optional calibration from
  the teacher's own marks; release / withdraw.
- Frontend: `pages/teacher/PaperResults.jsx` (ReleasePanel, results table, calibration), `components/AnswerSheetViewer.jsx`,
  `components/ui/StatLedger.jsx`, `ScoreMark.jsx`.
- Backend: `GET /api/results/paper/{id}` (`routers/results.py`); release `PUT /api/papers/{id}/release`
  (`routers/papers.py`); calibration `PUT /api/papers/{id}/calibration/marks/{sub}`, `POST .../calibration/apply`,
  `DELETE .../calibration` (`routers/calibration.py`, `pipeline/calibration.py fit / apply`); marks changes
  `services/marks.py`.
- Tests: `test_results.py`, `test_release.py`, `test_calibration.py`, `test_calibration_api.py`, `test_marks.py`,
  `PaperResults.test.jsx`.

### 4.8 TA review and re-evaluation
- Two tabs: "Flagged by AI" (questions the pipeline flagged, each with a reason) and "Re-evaluation requests";
  the review page shows photos, readings, AI marks, keys and reference PDFs; TA marks are final with history.
- Frontend: `pages/ta/Dashboard.jsx`, `pages/ta/Review.jsx`, `hooks/useTa.js`.
- Backend: `routers/ta.py` (queues `FLAGGED` / `REEVAL`, items, marks), `services/marks.py`, `services/access.py`
  (TA sees only their subjects).
- Tests: `test_ta.py`, `frontend/src/pages/ta/__tests__/`.

### 4.9 Student results and re-evaluation request
- Marks only after release ("awaiting release" before), section breakdown, question-wise marks, written-answer
  breakdown per rubric point, marks history; one re-evaluation request per paper.
- Frontend: `pages/student/Result.jsx`, `components/results/MarkBreakdown.jsx`, `components/results/EvaluationNotice.jsx`.
- Backend: `GET /api/results/{id}` (`routers/results.py`), `POST /api/submissions/{id}/reevaluation`,
  `services/access.student_status` and `results_released`.

### 4.10 Dummy data
- Five Physics papers and 45 sheets from the labelled sets in every state (evaluated, flagged, TA done, re-evaluation,
  waiting). `python -m app.db.demo_data [--clear]` from `backend/`.
- Code: `backend/app/db/demo_data.py`. Tests: `test_demo_data.py`.

### 4.11 Look and feel
- "Marked paper" style, no emoji (enforced by `frontend/src/__tests__/no-emoji.test.js`).
- Code: `components/ui/*`, `components/layout/*`, `tailwind.config.js`, `src/index.css`, `utils/formatters.js`.

---

## 5. The marking pipeline, file by file

Entry points: `orchestrator.read_sheet` (stage 1) and `orchestrator.grade_sheet` (stage 2); `orchestrator.run`
does both for one-shot use. Everything is in `backend/app/pipeline/` unless noted.

| Step | What | File / function |
|---|---|---|
| Question list | Q1.. for MCQ, N1.. numerical, S1.. written; each written question also accepts the other numbering (S1 or Q21) | `readers.questions_for`, `readers.Question` |
| Photo clean-up and quality gate | rotation, paper edge, perspective, deskew; blur / glare / dark / contrast / resolution; blank pages skipped | `quality.py` (`find_page`, `warp_page`, `measure`, `text_ink_fraction`) |
| OMR with template | align photo to the blank (ORB + homography), darkness per bubble minus the blank's own, per-sheet offset, threshold 0.10 | `omr_template.py` (`align`, `read_sheet`); called by `orchestrator._read_omr_template` |
| OMR fallback | layout-free bubble reader, every question flagged | `services/omr_engine.py`; `orchestrator._read_omr` |
| Handwritten MCQ / numerical | readers A (Gemma) and B (Qwen) read each page; C (GLM-OCR) if they disagree; 2 of 3 | `page_reading.read_closed_form`, `decide`, `merge_pages`; `orchestrator._read_handwritten` |
| Written answers | Qwen (JSON) and Gemma (plain text with [[Qnn]] markers) transcribe each page by label | `page_reading.transcribe_subjective`, `split_marked`, `items_from_page_json`, `merge_attempts`, `subjective_texts`, `transcription_labels`, `norm_label` |
| No written answers on the sheet | all written questions flagged ("check the numbering") | `orchestrator.flag_missing_written` |
| MCQ and numerical marks | exact set match; numbers within tolerance, unit ignored; negative marking | `scoring.py` (`grade_mcq`, `grade_numerical`), `numeric.py` |
| Written-answer grading | Gemma, prompt v2, per rubric point present / partial / absent + evidence + confidence; marks summed in code; mandatory rule; evidence check | `grader.py` (`grade`, `score`, `quote_in`); prompt `prompts/prompt_pipeline.grade_prompt_v2` |
| Calibration | per-question shift from the teacher's marks | `calibration.py` |
| TA reasons | quality, readers, OMR margin, all options filled, numbers, grader | `routing.py`; collected in `orchestrator._grade` |
| Random quality check | 5 % of accepted written answers | `services/evaluator.add_spot_checks` |
| Model calls | role → model from `infra/models.yaml`, endpoints file, health cache, least-busy copy, too-long resend, token meter | `llm.py` (`resolve`, `chat`, `pick_url`, `copies`, `UsageMeter`) |
| Prompts | page reading, transcription, grading, answer key, OMR labels | `backend/app/prompts/prompt_pipeline.py` (`TEMPLATE_VERSION`) |
| Edit distance | CER / WER for evaluation | `textdist.py` |
| Older paths | single-model Ollama reader and grader, crop segmentation | `services/ollama_engine.py`, `services/subjective_grader.py`, `readers.segment`, `prompts/prompt_extraction.py`, `prompts/prompt_subjective_grading.py` |

Tests: `test_pipeline_logic.py`, `test_pipeline_flow.py`, `test_page_reading.py`, `test_grading_logic.py`,
`test_quality_gate.py`, `test_omr_template.py`, `test_llm.py`, `test_inference_options.py`.

---

## 6. Data

### MongoDB (`backend/app/db/mongodb.py`)

| Collection | Holds | Written by |
|---|---|---|
| `users` | role, email or roll_no, name, subject(s), password hash | `db/seed.py` |
| `papers` | type, counts, marks, answer keys, rubrics, file URLs, `omrTemplate`, `answerSheetFormat`, `resultsReleased`, calibration | `routers/papers.py`, `routers/calibration.py` |
| `submissions` | pages, sheet type, status, batch_id, `read_state`, result, per-question details, review flags, `ta_review`, `reevaluation`, `marks_history` | `routers/submissions.py`, `services/evaluator.py`, `routers/ta.py`, `services/marks.py` |
| `batches` | paper, status, stage, total, times, error | `services/batch_runner.py` |

Sheet statuses: submitted → queued → reading → read → grading → evaluated (or error, which can be sent again).

### Files
- Student photos: `backend/uploads/<submission>_p<i>.<ext>`; paper PDFs and blank OMR sheets: `backend/uploads/papers/`.
- On the cluster: MongoDB data `/scratch/$USER/evalify/mongo-db`, password `/scratch/$USER/evalify/run/mongo.env`,
  endpoints file `/scratch/$USER/evalify/run/endpoints.json`, logs `/scratch/$USER/evalify/logs/`.

---

## 7. Model serving and cluster scripts

| File | Purpose |
|---|---|
| `infra/models.yaml` | models (repo, pinned revision, size, flags), serving profiles (`tier1` production: Gemma on the A6000, Qwen + GLM-OCR + second Gemma on the PRO 6000; `tier1-single`; `opt-*` experiments), roles |
| `infra/cluster/env.sh` | paths and caches on `/scratch`; source it everywhere |
| `infra/cluster/setup_vllm_env.sh` | creates the pinned vLLM conda environment |
| `infra/cluster/download_models.py` | downloads pinned model weights |
| `infra/cluster/serve.py` | places one vLLM server per model on the GPUs (92 % of real card size), writes the endpoints file |
| `infra/cluster/serve_models.sbatch` | production Slurm job on cn07 (2 GPUs) |
| `infra/cluster/serve_switch.sbatch` | experiment job whose profile can be switched without releasing the GPUs |
| `infra/cluster/mongo.sh` | MongoDB in user space (`init`, `start`, `stop`, `status`) |
| `infra/cluster/app.sh` | starts MongoDB, backend (47823) and frontend (5173) on the login node |
| `docker-compose.dev.yml` | local MongoDB + MLflow with Docker (its backend/frontend services are the old Ollama version) |

---

## 8. Evaluation harness and reports (`eval/`)

| Group | Files |
|---|---|
| Labelled data | `data/own_omr`, `own_mcq`, `own_mcqnum` (your 45 photos), `data/mendeley`, `data/edu_circuit`, `data/example`; loader `dataset.py`; format in `eval/README.md` |
| Building data | `make_test_papers.py`, `extract_test_photos.py`, `build_mendeley.py`, `make_example.py`, `make_upload_kit.py`, `reference_material_text.py` |
| Model choice | `reader_bakeoff.py`, `grader_bakeoff.py`, `mendeley_readers.py`, `make_mendeley_report.py`, `arch_sweep.py`, `mendeley_sweep.py`, `edu_circuit.py`, `edu_read_accuracy.py` |
| Grading and calibration | `mendeley_seg.py`, `mendeley_calibrate.py`, `mendeley_marks_table.py`, `mendeley_strictness.py`, `exp_consistency.py`, `exp_fewshot_shift.py`, `exp_routing.py`, `calibrate.py` |
| OMR | `tamaulipas_omr.py` |
| Speed and cost | `exp_tokens.py`, `exp_throughput.py`, `cost_compare.py`, `scenario_cost.py`, `exp_inference.py`, `run_inference_steps.sh` |
| Whole system | `end_to_end.py`, `metrics.py` |
| Reports | `eval/reports/<experiment>/` (one folder per run) and the index `eval/reports/RESULTS.md` |

---

## 9. Tests

- Backend: `backend/tests/` (pytest; in-memory MongoDB via `mongomock-motor`, models stubbed; `conftest.py` seeds
  the users of `tests/fixtures/demo_test.env`; `helpers.py` creates papers and evaluated sheets).
  Run: `pytest tests/ -q` in `backend/`.
- Frontend: `__tests__/` folders next to the code (Vitest + Testing Library); mock API in `src/test/mockApi.js`,
  set-up in `src/test/setup.js`, render helpers in `src/test/utils.jsx`. Run: `npm test` in `frontend/`.
- CI: `.github/workflows/backend-tests.yml`, `frontend-build.yml`, `frontend-lint.yml`, `docker-build.yml`.

---

## 10. Documents

| File | Content |
|---|---|
| `README.md` | setup on a new machine and on the cluster, configuration, directory layout |
| `Architecture Diagram/` | high level design, diagrams, sequence diagrams, JPG images, hand-drawn scripts in `sketch/` |
| `V2_EVALIFY_PLAN.md` | the pipeline design |
| `EVALIFY_PLAN.md`, `Phase0.md` to `Phase6.md` | original plan and phase notes |
| `evalify_model_plan (1).md` | model and hardware plan |
| `INFERENCE_OPTIMIZATION.md` | speed experiments and results |
| `dataset.md` | datasets and licence limits |
| `decision.md` | every decision and discussion, with dates |
| `MANUAL_CHECKLIST.md` | manual test checklist |
| `uploads/README.md` | how to use the upload kit |
| `eval/README.md`, `eval/reports/RESULTS.md` | evaluation harness and all results |

---

## 11. Where to change things

| To change | Edit |
|---|---|
| Which model does what, or the GPU layout | `infra/models.yaml` (roles, profiles), then restart the GPU job |
| A prompt | `backend/app/prompts/prompt_pipeline.py` (bump `TEMPLATE_VERSION`, re-measure with `eval/exp_inference.py`) |
| When a question goes to a TA | `backend/app/pipeline/routing.py` (thresholds can be overridden by an optional `infra/routing.yaml`) |
| MCQ / numerical marking rules | `backend/app/pipeline/scoring.py`, `numeric.py` |
| Written-answer marking | `backend/app/pipeline/grader.py` |
| OMR reading | `backend/app/pipeline/omr_template.py` |
| Photo checks | `backend/app/pipeline/quality.py` |
| Batch size or stages | `backend/app/services/batch_runner.py` (`EVALIFY_BATCH_CONCURRENCY`) |
| Users and subjects | `demo.env` (restart the backend) |
| A screen | `frontend/src/pages/<role>/`; shared parts in `frontend/src/components/` |
| Colours and fonts | `frontend/tailwind.config.js`, `frontend/src/index.css` |
| Settings | `backend/app/config.py` and environment variables (README, configuration reference) |
