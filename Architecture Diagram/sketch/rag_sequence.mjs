// rag_sequence.mjs — the answer-key assistant (RAG) as a sequence diagram in the Excalidraw style.
//   VIRGIL_FONT=/path/Virgil.woff2 node rag_sequence.mjs out.png
import { canvas, render } from "./sketch_lib.mjs";

const P = [["T", "Teacher", "person"], ["W", "Web app", "app"], ["B", "Backend", "app"], ["S", "Search|(BM25)", "app"], ["G", "Gemma", "model"]];
const GAP = 270, LEFT = 120, TOP = 40, BW = 170, BH = 70, STEP = 80;
const X = Object.fromEntries(P.map(([id], i) => [id, LEFT + i * GAP]));
const c = canvas(X.G + 160, 1110, { flat: true });

// Participants and dashed lifelines
for (const [id, label, kind] of P) {
  c.line(X[id], TOP + BH, X[id], c.H - 30, 'stroke-dasharray="10 10"', { strokeWidth: 1.5, stroke: "#9a9a9a" });
  c.box(X[id] - BW / 2, TOP, BW, BH, label, kind, 22);
}

let y = TOP + BH + 70, n = 0;
const msg = (from, to, label, dashed = false) => {
  c.arrow(X[from], y, X[to] + (X[to] > X[from] ? -4 : 4), y, { dashed, label, labelDy: -28 });
  c.step(X[from], y, ++n);
  y += STEP;
};

msg("T", "W", "Upload notes, paste the questions");
msg("W", "B", "Draft answer key");
msg("B", "S", "Notes split into passages (file + page)");

// Per-question loop
const top = y - 45;
y += 40;
msg("B", "S", "Find the 5 best passages");
msg("S", "B", "5 passages", true);
msg("B", "G", "Question + passages (use only these)");
msg("G", "B", "Answer + rubric points citing passages", true);
c.frame(X.B - 60, top, X.G - X.B + 150, y - top - 30, "for each question");
y += 10;

msg("B", "W", "Drafts with sources", true);
msg("W", "T", "Check, edit, use in the rubric", true);

// Note: what the draft is used for
const w = 560;
c.draw(c.gen.rectangle(X.W - 40, y - 20, w, 70, c.opt(c.fillOf("note"))));
c.text(X.W - 40 + w / 2, y + 15, "Drafts never mark students.|Only the rubric the teacher approves is used.", 19);

await render(c, process.argv[2] || "rag_sequence.png");
console.log("drawn rag_sequence");
