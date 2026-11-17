# Evalify

Evalify marks photographed exam answer sheets. Teachers create a paper (question paper, answer key, rubrics),
students upload photos of their handwritten sheets, and the teacher starts the evaluation. The system reads every
sheet with vision-language models, marks MCQ and numerical answers in code, grades written answers against the
rubric, and sends the questions it is unsure of to a TA. The teacher releases the final marks to the students.

## Contents

1. [How it works](#how-it-works)
2. [Requirements](#requirements)
3. [Setup on a new machine](#setup-on-a-new-machine)
4. [Setup on the IIT Jodhpur GPU cluster](#setup-on-the-iit-jodhpur-gpu-cluster)
5. [Using the app](#using-the-app)
6. [Running the tests](#running-the-tests)
7. [Configuration reference](#configuration-reference)
8. [Directory layout](#directory-layout)
9. [Troubleshooting](#troubleshooting)
10. [Further documentation](#further-documentation)

---

## How it works

### Roles

| Role | Logs in with | Can do |
|---|---|---|
| Teacher | email + password | Create papers, start evaluation, view and hand-mark results, release marks |
| TA | email + password | Review questions flagged by the system, answer re-evaluation requests |
| Student | roll number + password | Upload answer sheets, see released marks, ask for re-evaluation |

### Paper types

| Type | Questions | How they are marked |
|---|---|---|
| 1 | MCQ only (OMR bubble sheet or handwritten) | Bubble detection in code, or vision models reading the page |
| 2 | MCQ + numerical | Vision models read the answers; code compares them with the key (value within tolerance, unit ignored) |
| 3 | MCQ + numerical + written answers | As type 2, plus written answers transcribed and graded against the rubric |

### Evaluation flow

```
Student uploads photos ──► stored (status "submitted"), nothing is read yet

Teacher clicks "Start evaluation"
   └─► one batch with every waiting sheet of the paper
         Stage 1, reading (32 sheets at a time)
            quality check of the photos (code)
            OMR sheets: bubble detection (code)
            MCQ / numerical: reader A (Gemma) and reader B (Qwen) read each page;
                             if they disagree, reader C (GLM-OCR) decides (2 of 3)
            written answers: transcribed by Qwen and by Gemma
         Stage 2, grading (32 sheets at a time)
            MCQ / numerical marks: compared with the answer key (code)
            written answers: graded by Gemma against the rubric (transcripts only)
            review flags: unsure questions go to the TA, each with one reason
   └─► TA reviews flagged questions ──► teacher releases marks ──► students see them
```

### Components

```
Browser ──► Frontend (React + Vite, port 5173)
               │  /api is proxied
               ▼
            Backend (FastAPI, port 47823) ──► MongoDB (papers, submissions, users, batches)
               │                          └─► MLflow (optional, one run per evaluated sheet)
               ▼
            Model servers (vLLM, OpenAI-compatible API, one server per model on the GPUs)
               Gemma 4 31B FP8   reader A, transcriber, grader (two copies, each request to the less busy one)
               Qwen 3.8 27B FP8  reader B, transcriber
               GLM-OCR           reader C (tie-breaker)
```

The backend finds the model servers through an endpoints file written by the GPU job (see
[Model servers](#model-servers)). If no model server is reachable, OMR sheets are still marked (they need no
model); handwritten sheets end with an error and can be evaluated again once the models are up.

---

## Requirements

| Part | Needed for | Version |
|---|---|---|
| Python | backend, tests, evaluation scripts | 3.11 |
| Node.js + npm | frontend | Node 18 or newer (tested with 22) |
| MongoDB | data | 7.x (Docker, a system install or the user-space script for the cluster) |
| NVIDIA GPUs + CUDA driver | model servers, only for handwritten sheets | About 135 GB of GPU memory for the production layout `tier1` (one 48 GB and one 96 GB card); `tier1-single` drops the second Gemma copy |
| Conda + vLLM | model servers | vLLM 0.32.0 (pinned in `infra/cluster/env.sh`) |
| Disk | model weights | About 70 GB for the three production models |
| Docker (optional) | quick local MongoDB + MLflow | 20.10+ with Compose v2 |

Without GPUs you can still run the whole app: log in with every role, create papers, upload sheets, mark OMR
sheets, and use the TA and release screens with the dummy data.

---

## Setup on a new machine

These steps work on any Linux or macOS machine. Steps 1 to 6 give a working app; step 7 adds the models for
handwritten sheets.

### 1. Get the code

```bash
git clone <repository-url> Evalify
cd Evalify
git checkout pipeline-v2          # current development branch
```

### 2. Start MongoDB

Pick one option.

**Option A, Docker (simplest):**

```bash
docker compose -f docker-compose.dev.yml up -d mongodb mlflow
```

This starts MongoDB on `localhost:27017` (user `evalify`, password `evalify_dev_pass`, the backend's default) and
MLflow on `http://localhost:5005`. Start only these two services: the `backend` and `frontend` services in that
file are from the older Ollama-based version.

**Option B, MongoDB installed on the machine:** create a user and set `MONGO_URI` before starting the backend:

```bash
export MONGO_URI="mongodb://<user>:<password>@localhost:27017/evalify_db?authSource=admin"
```

**Option C, no database at all (quick look only):** start the backend with `EVALIFY_INMEMORY_DB=1`. Everything
is lost when the backend stops.

### 3. Set up the backend

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Start the backend

```bash
# still in backend/, with the venv active
export EVALIFY_PIPELINE=v2                     # use the model pipeline (see Configuration reference)
uvicorn app.main:app --host 127.0.0.1 --port 47823 --reload
```

Check it at `http://localhost:47823/api/health` (returns `{"status":"ok",...}`) and see the API at
`http://localhost:47823/docs`.

On start-up the backend creates the demo teachers, TAs and students listed in `demo.env` (see
[Using the app](#using-the-app)) and resumes any evaluation batch that was cut off by a restart.

### 5. Set up and start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The dev server forwards every `/api` call to the backend on port 47823, so no
backend URL needs to be configured.

### 6. Load the dummy data (optional)

Fills the Physics teacher's account with five papers and 45 answer sheets built from our own labelled sets
in `eval/data/own_*`, in every state (evaluated, flagged for the TA, TA done, re-evaluation pending and
resolved, waiting for evaluation):

```bash
cd backend
python -m app.db.demo_data            # load (safe to run again; replaces the previous dummy data)
python -m app.db.demo_data --clear    # remove it again (real papers and sheets are never touched)
```

Log in as `physics.teacher@evalify.local` / `Teacher@123` to see it. Students PH2025001 to PH2025015 hold the
sheets (PH2025001 to PH2025005 have sheets on all five papers).

### 7. Model servers (only for handwritten sheets)

Skip this step if you only need the UI or OMR sheets.

The models are served with vLLM, one server per model. All model details (Hugging Face repository, pinned
revision, size, server flags) and the serving layouts ("profiles") are in `infra/models.yaml`. The scripts below
were written for the cluster (Slurm, `/scratch`) but work on any GPU machine once the paths in
`infra/cluster/env.sh` are adjusted.

**a. Point the caches at a large disk.** Edit `infra/cluster/env.sh` (or export the variables before sourcing
it):

```bash
export EVALIFY_HOME=/path/to/Evalify
export EVALIFY_SCRATCH=/path/to/large/disk/evalify     # weights, caches, logs, endpoints file
source infra/cluster/env.sh
```

**b. Create the vLLM environment** (needs conda and internet, takes a while):

```bash
bash infra/cluster/setup_vllm_env.sh
```

**c. Download the production models** (Qwen, Gemma, GLM-OCR; each pinned to the revision in `models.yaml`):

```bash
"$VLLM_ENV/bin/python" infra/cluster/download_models.py --only qwen38-27b-fp8
"$VLLM_ENV/bin/python" infra/cluster/download_models.py --only gemma4-31b-fp8
"$VLLM_ENV/bin/python" infra/cluster/download_models.py --only glm-ocr
"$VLLM_ENV/bin/python" infra/cluster/download_models.py --list        # check what is on disk
```

**d. Start the servers.** With Slurm:

```bash
sbatch infra/cluster/serve_models.sbatch            # profile tier1 (production)
```

Without Slurm, run the same launcher directly on the GPU machine:

```bash
source infra/cluster/env.sh
"$VLLM_ENV/bin/python" infra/cluster/serve.py tier1
```

When the servers are up, the launcher writes `$EVALIFY_SCRATCH/run/endpoints.json` with the address of each
model. Model loading takes a few minutes.

**e. Tell the backend where the endpoints file is**, then restart the backend:

```bash
export EVALIFY_ENDPOINTS_FILE=/path/to/large/disk/evalify/run/endpoints.json
```

Alternatively, point at each server by hand, for example
`EVALIFY_ENDPOINT_GEMMA4_31B_FP8=http://gpu-host:8111/v1` (one variable per model name in `models.yaml`).

---

## Setup on the IIT Jodhpur GPU cluster

The cluster has no Docker and no root access, and the GPU node (cn07) reads the home directory very slowly. So
everything heavy lives on `/scratch/$USER/evalify`, MongoDB runs in user space on the login node, and the models
run as a Slurm job on cn07.

### One-time setup

```bash
cd ~/Evalify
source infra/cluster/env.sh                       # paths and caches on /scratch

# 1. Backend Python environment on /scratch
python3.11 -m venv /scratch/$USER/evalify/envs/backend
/scratch/$USER/evalify/envs/backend/bin/pip install -r backend/requirements.txt

# 2. MongoDB in user space: unpack the MongoDB 7.0 tarball for RHEL 8 (x86_64) from mongodb.com into
#    /scratch/$USER/evalify/mongodb/ so that mongodb/mongodb-linux-*/bin/mongod exists, then:
bash infra/cluster/mongo.sh init                  # creates the evalify user with a random password

# 3. Frontend packages
(cd frontend && npm install)

# 4. vLLM environment and model weights (login node, has internet)
bash infra/cluster/setup_vllm_env.sh
"$VLLM_ENV/bin/python" infra/cluster/download_models.py --only qwen38-27b-fp8
"$VLLM_ENV/bin/python" infra/cluster/download_models.py --only gemma4-31b-fp8
"$VLLM_ENV/bin/python" infra/cluster/download_models.py --only glm-ocr
```

`mongo.sh init` stores the generated password only in `/scratch/$USER/evalify/run/mongo.env` (readable by you
only). MongoDB listens on `127.0.0.1:27027` with authentication on, because other users share the login node.
Never copy that password into the repository.

### Every time

```bash
# Models on 2 GPUs of cn07 (runs up to 36 h; writes /scratch/$USER/evalify/run/endpoints.json)
sbatch infra/cluster/serve_models.sbatch
squeue -u $USER                                   # wait until the job is RUNNING
cat /scratch/$USER/evalify/run/endpoints.json     # models appear here as they come up

# Database + backend + frontend on the login node
bash infra/cluster/app.sh start
bash infra/cluster/app.sh status
bash infra/cluster/app.sh stop                    # backend and frontend (MongoDB keeps running)
```

Open the app through VS Code port forwarding (ports 5173 and 47823), or with SSH from your own computer:

```bash
ssh -L 5173:localhost:5173 -L 47823:localhost:47823 <user>@<login-node>
```

Logs are in `/scratch/$USER/evalify/logs/` (`backend.log`, `frontend.log`, `mongod.log`, `serve-<job>.out`).

Cluster rules we follow: at most 2 GPUs per user; release the GPU job (`scancel <job id>`) when you are done so
other users can use the node.

---

## Using the app

### Demo accounts

The accounts come from `demo.env` and are created or updated each time the backend starts. They use fake
credentials, for testing only. To add users, edit `demo.env` and restart the backend (the file explains the
format).

| Role | Login | Password | Subject |
|---|---|---|---|
| Teacher (two subjects) | `teacher@evalify.local` | `Teacher@123` | Computer Science and Data Science |
| Teacher | `physics.teacher@evalify.local` | `Teacher@123` | Physics |
| Teacher (two subjects) | `science.teacher@evalify.local` | `Teacher@123` | Physics and Mathematics |
| Teacher | `maths.teacher@evalify.local` | `Teacher@123` | Mathematics |
| Teacher | `ds.teacher@evalify.local` | `Teacher@123` | Data Science |
| TA | `ta.physics@evalify.local` (others in `demo.env`) | `Ta@12345` | Physics |
| Student | `CS2025001` ... `CS2025030` | `Student@123` | Computer Science |
| Student | `PH2025001` ... `PH2025020` | `Student@123` | Physics |
| Student | `MA2025001` ... `MA2025015` | `Student@123` | Mathematics |
| Student | `DS2025001` ... `DS2025048` | `Student@123` | Data Science |

### A typical round

1. **Teacher** creates a paper: uploads the question paper PDF, the answer key, and for written answers the
   rubric. The answer-key assistant can draft reference answers for written questions.
2. **Students** upload photos of their answer sheets. The sheets are stored and wait.
3. **Teacher** opens the paper's results page and clicks **Start evaluation**. The panel shows stage 1
   (reading) and stage 2 (grading) with counts.
4. **TA** works through the "Flagged by AI" tab: each item shows the photo, what the models read and why it was
   flagged.
5. **Teacher** releases the marks. Students see their marks and can ask for re-evaluation, which goes to the TA.

The folder `uploads/` holds a ready-made upload kit (question papers, answer keys and sheet photos for each paper
type) for trying every flow by hand.

---

## Running the tests

Neither test suite needs MongoDB, GPUs or model servers: the backend tests use an in-memory database and stub
the models.

```bash
# Backend (from backend/, venv active)
pytest tests/ -q

# Frontend (from frontend/)
npm test            # Vitest, run once
npm run lint
npm run build       # production build check
```

The same checks run on GitHub Actions when changes are pushed to `main` (`.github/workflows/`).

---

## Configuration reference

The backend reads its settings from environment variables (`backend/app/config.py`). The defaults suit local
development.

| Variable | Default | Purpose |
|---|---|---|
| `MONGO_URI` | `mongodb://evalify:evalify_dev_pass@localhost:27017/evalify_db?authSource=admin` | Database connection |
| `MONGO_DB_NAME` | `evalify_db` | Database name |
| `EVALIFY_INMEMORY_DB` | off | Run without MongoDB (data lost on restart) |
| `TEACHER_JWT_SECRET`, `STUDENT_JWT_SECRET`, `TA_JWT_SECRET` | placeholder strings | Login token signing; **set your own values on any shared machine** |
| `EVALIFY_DEMO_ENV` | `demo.env` in the repo root | File with the demo users |
| `EVALIFY_PIPELINE` | `auto` | `v2`: always use the model pipeline; `legacy`: old single-model path; `auto`: pipeline when a model is reachable |
| `EVALIFY_ENDPOINTS_FILE` | `/scratch/$USER/evalify/run/endpoints.json` | Where the GPU job publishes the model addresses |
| `EVALIFY_ENDPOINT_<MODEL>` | not set | Address of one model server by hand, for example `EVALIFY_ENDPOINT_GLM_OCR=http://host:8104/v1` |
| `EVALIFY_MODELS_YAML` | `infra/models.yaml` | Model registry and roles |
| `EVALIFY_LLM_TIMEOUT` | `600` | Seconds per model request |
| `EVALIFY_BATCH_CONCURRENCY` | `32` | Sheets in flight per stage of a batch |
| `EVALIFY_PIPELINE_WORKERS` | `8` | Parallel model requests within one sheet |
| `EVALIFY_SPOT_CHECK_RATE` | `0.05` | Share of auto-accepted written answers sent to a TA at random as a quality check |
| `MLFLOW_TRACKING_URI` | `http://localhost:5005` | MLflow server for run logging (logging is skipped if unreachable) |

JWT secrets can also be placed in `teacher_credentials.env` and `student_credentials.env` in the repository root.
These files are git-ignored; never commit real secrets.

---

## Directory layout

```
Evalify/
├── backend/                  FastAPI backend and the marking pipeline
├── frontend/                 React web app
├── infra/                    model registry and the scripts that run models, database and app
├── eval/                     evaluation harness, labelled data and experiment reports
├── Architecture Diagram/     high level design, Mermaid diagrams and sequence diagrams
├── uploads/                  upload kit for testing the app by hand
├── testing_data/             sample question paper and answer key PDFs
├── k8s/                      Kubernetes namespace (deployment not built yet)
├── .github/workflows/        CI: backend tests, frontend build and lint, Docker build
├── demo.env                  demo users (fake credentials)
├── docker-compose.dev.yml    local MongoDB and MLflow (Docker)
└── *.md                      plans, decisions and experiment write-ups (see Further documentation)
```

### backend/

```
backend/
├── app/
│   ├── main.py               FastAPI app: routers, CORS, database start-up, demo users, batch recovery
│   ├── config.py             settings from environment variables
│   ├── routers/              HTTP endpoints (all under /api)
│   ├── services/             application logic used by the routers
│   ├── pipeline/             the marking pipeline (readers, grader, scoring, review flags)
│   ├── prompts/              prompts and JSON schemas sent to the models
│   ├── models/               request and response schemas (Pydantic)
│   └── db/                   MongoDB connection, demo users, dummy data, MLflow logging
├── tests/                    pytest suite (in-memory database, stubbed models)
├── db/mongo-init.js          creates the database when the Docker MongoDB starts the first time
├── uploads/                  stored question papers and answer sheet photos
├── requirements.txt          Python packages
├── Dockerfile, start.sh      older Ollama-based container and start script
└── Ollama.md                 notes on the older Ollama set-up
```

| Folder | File | Purpose |
|---|---|---|
| `routers/` | `auth.py` | Login for teachers and TAs (email) and students (roll number); JWT tokens |
| | `papers.py` | Create, list and edit papers; PDF uploads; answer-key and rubric extraction; answer-key assistant |
| | `submissions.py` | Student uploads (stored until evaluation), page images, re-evaluation requests |
| | `evaluation.py` | Teacher's "Start evaluation" and its progress |
| | `results.py` | Results per paper (teacher) and per sheet (student, teacher, TA); release |
| | `ta.py` | TA subjects, "Flagged by AI" and "Re-evaluation requests" tabs, final marks |
| | `calibration.py` | Optional teacher calibration of written-answer marks |
| `services/` | `batch_runner.py` | Runs a batch: stage 1 reads every sheet, stage 2 grades them; resumes after a restart |
| | `evaluator.py` | Evaluates one sheet (in one go or in the two batch stages) and saves the result |
| | `access.py` | Who may see a sheet: its student, the paper's teacher, or a TA of the subject |
| | `marks.py` | Mark changes after evaluation (TA, teacher hand-marking, calibration) with history |
| | `answer_key.py` | Answer-key assistant: drafts reference answers for written questions |
| | `rubric_extractor.py` | Turns the teacher's PDFs into per-question rubrics |
| | `omr_engine.py` | Bubble detection for OMR sheets (OpenCV) |
| | `pdf_utils.py` | PDF rendering and text extraction (PyMuPDF) |
| | `ollama_engine.py`, `subjective_grader.py` | Older Ollama path, kept as a fallback |
| `pipeline/` | `orchestrator.py` | The pipeline for one sheet: `read_sheet` (stage 1) and `grade_sheet` (stage 2) |
| | `quality.py` | Photo clean-up (rotation, perspective, deskew) and quality check (blur, glare, darkness, contrast) |
| | `page_reading.py` | Whole-page reading of MCQ / numerical answers and transcription of written answers |
| | `readers.py` | The `Reading` record and reader helpers |
| | `scoring.py`, `numeric.py` | MCQ and numerical marking in code (tolerance, unit ignored) |
| | `grader.py` | Rubric grading of one written answer |
| | `routing.py` | Which questions go to the TA, and why |
| | `calibration.py` | Applies the teacher's calibration |
| | `omr_template.py` | OMR from a blank template sheet (any layout) |
| | `llm.py` | Finds the model server for each role, sends requests, counts tokens |
| | `textdist.py` | Character and word error rates |
| `db/` | `mongodb.py` | Database connection and collections |
| | `seed.py`, `demo_users.py` | Creates the users listed in `demo.env` |
| | `demo_data.py` | Dummy papers and sheets from `eval/data/own_*` |
| | `mlflow_logger.py` | Logs each evaluation to MLflow |

### frontend/

```
frontend/
├── src/
│   ├── main.jsx, App.jsx     entry point and routes per role
│   ├── pages/auth/           login pages
│   ├── pages/teacher/        dashboard, create paper (wizard), paper results, release
│   ├── pages/ta/             TA queues and the review screen
│   ├── pages/student/        subjects, paper upload, results, re-evaluation
│   ├── components/ui/        buttons, cards, badges, inputs (the "marked paper" look)
│   ├── components/layout/    page frame and navigation
│   ├── components/forms/     paper wizard steps, upload forms, answer-key assistant
│   ├── components/results/   result tables, Start evaluation panel, release panel, notices
│   ├── hooks/                data loading (papers, submissions, TA, auth)
│   ├── store/                login state and toasts (Zustand)
│   ├── services/api.js       Axios client for /api with the login token
│   ├── utils/                formatters and form validators
│   └── test/                 test set-up and the mock API
├── vite.config.js            dev server on 5173, /api proxied to the backend on 47823
├── tailwind.config.js        colours and fonts
└── package.json              scripts: dev, build, test, lint
```

Tests sit next to the code in `__tests__/` folders. `src/__tests__/no-emoji.test.js` fails the build if an emoji
appears anywhere in the app.

### infra/

| File | Purpose |
|---|---|
| `models.yaml` | Every model (repository, pinned revision, server flags), the serving profiles (which model goes on which GPU, with how much memory) and the roles (which model reads, transcribes and grades) |
| `cluster/env.sh` | Paths and caches on `/scratch`; source it in every shell and job |
| `cluster/setup_vllm_env.sh` | Creates the pinned vLLM conda environment |
| `cluster/download_models.py` | Downloads model weights at the pinned revisions |
| `cluster/serve.py` | Starts one vLLM server per model of a profile and writes the endpoints file |
| `cluster/serve_models.sbatch` | Slurm job that runs `serve.py` on 2 GPUs of cn07 (production) |
| `cluster/serve_switch.sbatch` | Slurm job whose profile can be changed without giving up the GPUs (experiments) |
| `cluster/mongo.sh` | MongoDB in user space on the login node (`init`, `start`, `stop`, `status`) |
| `cluster/app.sh` | Starts MongoDB, the backend and the frontend on the login node |

### eval/

The evaluation harness that chose the models and measured accuracy and speed. See `eval/README.md` for the
labelled-set format and how to run it.

| Path | Purpose |
|---|---|
| `data/own_omr`, `own_mcq`, `own_mcqnum` | Our own labelled basic-science sets (15 sheets each); also the dummy data |
| `data/mendeley`, `data/edu_circuit` | Public datasets, for internal evaluation only (see `dataset.md` for the licence limits) |
| `dataset.py`, `metrics.py` | Loading labelled sets and computing accuracy measures |
| `end_to_end.py` | Runs the full pipeline on a labelled set and scores it |
| `reader_bakeoff.py`, `grader_bakeoff.py` | Model comparisons for reading and grading |
| `exp_*.py` | Single experiments (consistency, routing, throughput, tokens, inference speed) |
| `run_inference_steps.sh` | Runs the inference-speed experiments one profile after another |
| `make_*.py` | Builds test papers, examples and the upload kit |
| `reports/` | One report per run; `reports/RESULTS.md` lists every run with its result |
| `test_papers/` | Generated question papers and keys |

---

## Troubleshooting

| Problem | Check |
|---|---|
| Backend does not start: database connection error | Is MongoDB running? Docker: `docker ps`; cluster: `bash infra/cluster/mongo.sh status`. Is `MONGO_URI` right? |
| Handwritten sheets end with "no reader model is reachable" | Are the model servers up? Look at the endpoints file and `curl <base_url>/models`. Does `EVALIFY_ENDPOINTS_FILE` point to the file the GPU job writes? Restart the backend after changing it |
| "Start evaluation" is greyed out | No sheet of that paper is waiting, or a batch is already running |
| A model server does not start | Read its log in `$EVALIFY_LOG_DIR`. "KV cache is needed ... available" means the profile gives the model too little memory: lower `--max-model-len` or raise its `gb` in `models.yaml` |
| GPU job stays PENDING | The GPUs are in use by others; `squeue -w cn07` shows who |
| Port already in use | `lsof -i :47823` (or `:5173`), stop that process, or `bash infra/cluster/app.sh stop` |
| Frontend shows network errors | Is the backend running on 47823? The Vite proxy expects it there |

---

## Further documentation

| File | Content |
|---|---|
| `CODE_MAP.md` | The whole flow and where every feature's code lives (screens, endpoints, backend files, tests) |
| `Architecture Diagram/` | High level design, Mermaid structure diagrams and sequence diagrams of the whole system |
| `V2_EVALIFY_PLAN.md` | The current pipeline design (readers, grader, review flags, answer-key assistant) |
| `EVALIFY_PLAN.md` | Original project plan and roadmap |
| `evalify_model_plan (1).md` | Model and hardware plan |
| `INFERENCE_OPTIMIZATION.md` | Speed experiments on the GPUs and their results |
| `dataset.md` | Datasets used for evaluation and their licence limits |
| `decision.md` | Log of every design decision, with the reason |
| `MANUAL_CHECKLIST.md` | Checklist for testing every part of the app by hand |
| `Phase0.md` ... `Phase6.md` | Phase-by-phase build notes of the first version |
| `eval/README.md` | Evaluation harness |
| `eval/reports/RESULTS.md` | Results of every evaluation run |
