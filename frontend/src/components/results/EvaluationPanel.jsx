// EvaluationPanel.jsx — the teacher's "Start evaluation": marks every submitted answer sheet of the paper as one
// batch (stage 1 reads all sheets, stage 2 grades them) and shows its progress, refreshing while it runs.

import { useCallback, useEffect, useRef, useState } from "react";
import api from "../../services/api";
import Card from "../ui/Card";
import Button from "../ui/Button";
import { formatDateTime } from "../../utils/formatters";

const POLL_MS = 5000;
const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;
const SLOW_S = 600;                                  // a batch with no finished sheet after this long is "taking longer than usual"

// "45 s" / "3 min 05 s" since an ISO time
function elapsedText(iso, now) {
  const s = Math.max(0, Math.floor((now - new Date(iso).getTime()) / 1000));
  return s < 60 ? `${s} s` : `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, "0")} s`;
}

// One stage as a ruled line: label, "done / total" and a thin bar
function StageLine({ label, done, total, active, testId }) {
  return (
    <div>
      <div className="flex justify-between text-sm">
        <span className={active ? "text-paper-900" : "text-paper-500"}>{label}</span>
        <span className="font-mono text-paper-700" data-testid={testId}>{done} / {total}</span>
      </div>
      <div className="h-px bg-paper-300 mt-1">
        {/* Active stage with nothing finished yet: a short pulsing bar shows the work has started */}
        <div className={`h-px bg-pen-500 ${active ? "animate-pulse" : ""}`}
             style={{ width: `${total && done ? (100 * done) / total : active ? 6 : 0}%` }} />
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
  // Clock for the "running for ..." line (every second while a batch runs)
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    if (!running) return undefined;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [running]);
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
  const finishedSheets = (c.evaluated ?? 0) + (c.error ?? 0);
  const elapsed = running && batch.created_at ? Math.floor((now - new Date(batch.created_at).getTime()) / 1000) : 0;

  return (
    <Card className="mb-6">
      <Card.Body className="space-y-4">
        <div className="flex flex-col md:flex-row md:items-center gap-4">
          <div className="flex-1">
            <p className="kicker">Evaluation</p>
            {running ? (
              <>
                <p className="text-paper-900 flex items-center gap-2">
                  <span className="inline-block w-2 h-2 rounded-full bg-pen-500 animate-pulse" aria-hidden="true" />
                  Evaluation is running
                </p>
                <p className="text-sm text-paper-700">
                  {batch.stage === "grading" ? "Stage 2 of 2: Grading answers" : "Stage 1 of 2: Reading answer sheets"}
                  {batch.created_at ? `, running for ${elapsedText(batch.created_at, now)}` : ""}
                </p>
              </>
            ) : batch?.status === "failed" ? (
              <p className="text-paper-900">Evaluation did not finish</p>
            ) : batch?.status === "done" && waiting === 0 ? (
              <p className="text-paper-900">Evaluation finished{batch.finished_at ? `, ${formatDateTime(batch.finished_at)}` : ""}</p>
            ) : (
              <p className="text-paper-900">
                {waiting ? `${plural(waiting, "answer sheet")} waiting for evaluation.` : "No answer sheets are waiting for evaluation."}
              </p>
            )}
            <p className="text-sm text-paper-500">
              {running
                ? "You can leave this page. The evaluation continues on the server and the results appear below when it finishes."
                : "Students' uploads are stored until you start. All sheets are read first, then graded together."}
            </p>
            {running && elapsed > SLOW_S && finishedSheets === 0 && (
              <p className="text-sm text-amber-700">
                This is taking longer than usual. The model servers may be busy or offline; if nothing changes,
                ask the administrator to check them.
              </p>
            )}
            {batch?.status === "failed" && (
              <p className="text-sm text-red-700">
                The last evaluation stopped: {batch.error || "unknown error"}. Sheets that were not finished are included
                again when you start evaluation.
              </p>
            )}
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
