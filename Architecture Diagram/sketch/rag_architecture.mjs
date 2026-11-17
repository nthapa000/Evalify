// rag_architecture.mjs — the answer-key assistant (RAG) pipeline as a block diagram in the Excalidraw style.
//   VIRGIL_FONT=/path/Virgil.woff2 node rag_architecture.mjs out.png
import { canvas, render } from "./sketch_lib.mjs";

const c = canvas(1500, 760, { flat: true });
const W = 230, H = 110;
// Top row, left to right: teacher's notes -> read -> split -> search
const row1 = 150, row2 = 470;
const xs = [60, 420, 780, 1140];
c.box(xs[0], row1, W, H, "Teacher's notes|PDF or text", "data");
c.box(xs[1], row1, W, H, "1. Read text|keep file + page", "app");
c.box(xs[2], row1, W, H, "2. Split into|~120-word passages", "app");
c.box(xs[3], row1, W, H, "3. BM25 search|top 5 per question", "app");
c.arrow(xs[0] + W, row1 + H / 2, xs[1] - 6, row1 + H / 2);
c.arrow(xs[1] + W, row1 + H / 2, xs[2] - 6, row1 + H / 2);
c.arrow(xs[2] + W, row1 + H / 2, xs[3] - 6, row1 + H / 2);

// Questions come in from above
c.box(xs[3] + 15, 10, W - 30, 70, "Written questions", "data", 20);
c.arrow(xs[3] + W / 2, 80, xs[3] + W / 2, row1 - 6);

// Bottom row, right to left: Gemma drafts -> teacher checks -> rubric
c.box(xs[3], row2, W, H, "4. Gemma drafts|answer + points|with citations", "model");
c.box(xs[2] - 60, row2, W + 60, H, "5. Teacher checks|and edits", "person");
c.box(xs[0] + 200, row2, W + 30, H, "Rubric saved|on the paper", "data");
c.arrow(xs[3] + W / 2, row1 + H, xs[3] + W / 2, row2 - 6, { label: "passages", labelDy: 0 });
c.arrow(xs[3], row2 + H / 2, xs[2] - 60 + W + 60 + 6, row2 + H / 2, { label: "draft", labelDy: -22 });
c.arrow(xs[2] - 60, row2 + H / 2, xs[0] + 200 + W + 30 + 6, row2 + H / 2, { label: "approved", labelDy: -22 });
c.arrow(xs[0] + 200 + (W + 30) / 2, row2 + H, xs[0] + 200 + (W + 30) / 2, row2 + H + 75);
c.text(xs[0] + 200 + (W + 30) / 2, row2 + H + 100, "used to grade students", 19);

// One-line rules under the title
c.text(750, 340, "Only the teacher's own material is used.  If it does not cover a question, the draft says so.", 19);

await render(c, process.argv[2] || "rag_architecture.png");
console.log("drawn rag_architecture");
