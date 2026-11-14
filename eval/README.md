# Evalify evaluation harness

Measures how well each model reads and grades, picks the winners, and calibrates
when a question is sent to a TA (plan §10–12). All runs log to MLflow and write
CSV / JSONL files under `eval/runs/` (git-ignored).

## Labelled set format

One folder per set, e.g. `eval/data/midterm1/`:

```
manifest.jsonl          one line per answer sheet
papers/<paper>.json     the paper, same fields as the MongoDB paper document
images/<sheet>_p1.jpg   page photos / scans, in page order
```

A manifest line:

```json
{"sheet_id": "s017", "split": "dev", "paper": "papers/midterm1.json",
 "sheet_type": "handwritten", "pages": ["images/s017_p1.jpg", "images/s017_p2.jpg"],
 "gold": {
   "Q1": {"answer": "B"},
   "Q2": {"answer": "A,C"},
   "N1": {"answer": "0.625"},
   "S1": {"transcript": "Photosynthesis is the proccess where…",
          "marks": 3,
          "concepts": {"uses light energy": true, "produces glucose": true, "releases oxygen": false},
          "planted_errors": [{"wrong": "releases nitrogen", "correct": "releases oxygen"}],
          "crop": {"page": 0, "bbox": [40, 520, 960, 780]}}
 }}
```

- `answer`: what the student actually wrote (MCQ letters / number as written), **not** the key.
- `transcript`: exact hand transcription, mistakes included. Struck-out text as `~~x~~`, unreadable as `[?]`.
- `marks` / `concepts`: the TA's grading (double-graded sheets: put the agreed mark).
- `planted_errors`: deliberate **content** mistakes (wrong number, wrong fact, missing step) used to
  measure silent correction. Spelling is ignored — TAs don't mark it in university exams.
- `crop` (optional): answer box on a page, 0–1000 coordinates. Without it the segmenter finds the answer.
- `split`: freeze ~30 % as `test` and never tune on it.

Size: 30–50 sheets is enough to compare models; 150–300 double-graded sheets for final numbers.
`python eval/make_example.py` builds a 2-sheet synthetic set (`eval/data/example`) for smoke tests.

## Running the phases

Start the model servers first (`sbatch infra/cluster/serve_models.sbatch tier1-bakeoff`), then
from the repo root with the backend env (`/scratch/$USER/evalify/envs/backend/bin/python`):

| Phase | Command | Output |
|---|---|---|
| 0 baseline | `python eval/end_to_end.py <set> --legacy` | llama3.2-vision reference numbers |
| 2 readers | `python eval/reader_bakeoff.py <set>` | accuracy, CER/WER, over-correction per reader, shared-error rate per pair |
| 3 graders | `python eval/grader_bakeoff.py <set> [--thinking]` | QWK, MAE, per-concept accuracy on gold transcripts |
| 4 system | `python eval/end_to_end.py <set> --split dev` | coverage, auto-accept accuracy, silent errors, TA routing rate per paper type |
| 4 calibrate | `python eval/calibrate.py eval/runs/e2e_pipeline_dev_*.jsonl --target 0.98 --write` | `infra/routing.yaml` |
| report | `python eval/end_to_end.py <set> --split test` | final numbers on the frozen split |

After the bake-offs, set the winners in `infra/models.yaml` (`roles:` order and the `tier1`
profile) and delete losing weights with `infra/cluster/download_models.py --delete <name>`.
