// EvaluationNotice.jsx — the window a student sees until results are released:
// "Your answer sheet is being evaluated", while it is marked and while the teacher has not released results.

export default function EvaluationNotice({ status, paperName }) {
  const marking = status !== "awaiting_release";
  return (
    <section className="max-w-xl border border-paper-900 bg-paper-50 rounded-sm p-8">
      <p className="kicker">Status{paperName ? ` / ${paperName}` : ""}</p>
      <h2 className="font-serif text-2xl text-paper-900 mt-1">Your answer sheet is being evaluated</h2>
      {/* A thin moving rule instead of a spinner */}
      <div className="h-px bg-paper-300 my-5 overflow-hidden"><div className="h-px w-1/3 bg-pen-500 animate-pulse" /></div>
      <p className="text-sm text-paper-700">
        {marking
          ? "It is being read and marked now. This usually takes a few minutes."
          : "Marking is done. Your marks appear here once your teacher releases the results, after any answers that need a second look have been checked."}
      </p>
      <p className="text-xs text-paper-500 mt-3">You can leave this page; your result will be under the paper's subject.</p>
    </section>
  );
}
