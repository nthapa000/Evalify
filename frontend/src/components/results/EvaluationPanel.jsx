// EvaluationPanel.jsx — the teacher's "Start evaluation": marks every submitted answer sheet of the paper as one
// batch (stage 1 reads all sheets, stage 2 grades them) and shows its progress, refreshing while it runs.

import { useCallback, useEffect, useRef, useState } from "react";
import api from "../../services/api";
import Card from "../ui/Card";
import Button from "../ui/Button";
import { formatDateTime } from "../../utils/formatters";

const POLL_MS = 5000;
const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;

// One stage as a ruled line: label, "done / total" and a thin bar
function StageLine({ label, done, total, active, testId }) {
  return (
    <div>
      <div className="flex justify-between text-sm">
        <span className={active ? "text-paper-900" : "text-paper-500"}>{label}</span>
        <span className="font-mono text-paper-700" data-testid={testId}>{done} / {total}</span>
      </div>
      <div className="h-px bg-paper-300 mt-1">
        <div className="h-px bg-pen-500" style={{ width: `${total ? (100 * done) / total : 0}%` }} />
      </div>
    </div>
  );
}

export default function EvaluationPanel({ paperId, onFinished }) {
  const [state, setState] = useState(null);          // { waiting, batch }
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const reported = useRef(null);                     // batch id already reported as finished

  // Load waiting count + latest batch
  const load = useCallback(async () => {
    try {
      const { data } = await api.get(`/papers/${paperId}/evaluation`);
      setState(data);
    } catch (e) {
      setError(e.response?.data?.detail || "Could not load the evaluation status.");
    }
  }, [paperId]);

  useEffect(() => { load(); }, [load]);

  // Refresh while a batch runs; tell the page once when a batch has finished (its results table reloads)
  const batch = state?.batch;
  const running = batch?.status === "running";
  useEffect(() => {
    if (!running) return undefined;
    const t = setInterval(load, POLL_MS);
    return () => clearInterval(t);
  }, [running, load]);
  useEffect(() => {
    if (batch && batch.status !== "running" && reported.current !== batch.id) {
      reported.current = batch.id;
      onFinished?.();
    }
  }, [batch, onFinished]);

  // Queue every waiting sheet and start the batch
  const start = async () => {
    setBusy(true);
    setError("");
    try {
      const { data } = await api.post(`/papers/${paperId}/evaluate`);
      setState({ waiting: 0, batch: data });
    } catch (e) {
      setError(e.response?.data?.detail || "Could not start the evaluation.");
    } finally {
      setBusy(false);
    }
  };
  const waiting = state?.waiting ?? 0;
  const c = batch?.counts ?? {};
  const readDone = (c.read ?? 0) + (c.grading ?? 0) + (c.evaluated ?? 0) + (c.error ?? 0);
  const failed = c.error ?? 0;

  return (
    <Card className="mb-6">
      <Card.Body className="space-y-4">
        <div className="flex flex-col md:flex-row md:items-center gap-4">
          <div className="flex-1">
            <p className="kicker">Evaluation</p>
            {running ? (
              <p className="text-paper-900">
                {batch.stage === "grading" ? "Stage 2 of 2: Grading answers" : "Stage 1 of 2: Reading answer sheets"}
              </p>
            ) : batch?.status === "done" && waiting === 0 ? (
              <p className="text-paper-900">Evaluation finished{batch.finished_at ? `, ${formatDateTime(batch.finished_at)}` : ""}</p>
            ) : (
              <p className="text-paper-900">
                {waiting ? `${plural(waiting, "answer sheet")} waiting for evaluation.` : "No answer sheets are waiting for evaluation."}
              </p>
            )}
            <p className="text-sm text-paper-500">
              Students' uploads are stored until you start. All sheets are read first, then graded together.
            </p>
          </div>
          <Button onClick={start} loading={busy} disabled={!state || running || waiting === 0}>
            Start evaluation
          </Button>
        </div>

        {/* Progress of the current (or last) batch */}
        {batch && (
          <div className="space-y-3">
            <StageLine label="Reading answer sheets" done={readDone} total={batch.total}
                       active={running && batch.stage !== "grading"} testId="read-progress" />
            <StageLine label="Grading answers" done={c.evaluated ?? 0} total={batch.total}
                       active={running && batch.stage === "grading"} testId="grade-progress" />
          </div>
        )}
        {failed > 0 && (
          <p className="text-sm text-amber-700">
            {plural(failed, "sheet")} could not be evaluated; {failed === 1 ? "it is" : "they are"} included again
            when you start evaluation.
          </p>
        )}
        {error && <p className="text-sm text-red-700">{error}</p>}
      </Card.Body>
    </Card>
  );
}
