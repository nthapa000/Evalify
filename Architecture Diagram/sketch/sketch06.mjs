// Draw diagram 06 (one exam round) in the Excalidraw style: roughjs strokes + the Virgil handwriting font.
import fs from "node:fs";
import rough from "roughjs/bundled/rough.esm.js";
import puppeteer from "puppeteer";

const gen = rough.generator();
const FONT = fs.readFileSync(process.env.VIRGIL_FONT || "Virgil.woff2").toString("base64");
const INK = "#1e1e1e";
const KIND = { person: "#c9c2b6", app: "#8fb8de", model: "#94c99a", note: "#f5d97a" };

// Participants and messages (same content as the Mermaid diagram 06)
const P = [["T", "Teacher", "person"], ["S", "Student", "person"], ["TA", "TA", "person"], ["E", "Evalify", "app"], ["AI", "AI models", "model"]];
const M = [
  ["T", "E", "Create paper"],
  ["S", "E", "Upload answer sheet photos"],
  ["E", "S", "Submitted, waiting for evaluation", true],
  ["T", "E", "Start evaluation"],
  ["E", "AI", "Read handwritten sheets, grade written answers"],
  ["AI", "E", "Answers and grades", true],
  ["NOTE", "E", "MCQ, numerical and OMR are marked in code.|Doubtful answers go to the TA."],
  ["E", "T", "Results ready", true],
  ["TA", "E", "Check flagged answers, set final marks"],
  ["T", "E", "Release results"],
  ["S", "E", "Open result"],
  ["E", "S", "Marks and question-wise breakdown", true],
];

const GAP = 250, LEFT = 120, TOP = 40, BW = 170, BH = 64, STEP = 78;
const X = Object.fromEntries(P.map(([id], i) => [id, LEFT + i * GAP]));
X.AI += 140;                                      // more room for the longest label
const W = X.AI + BW / 2 + 60;
const rows = M.reduce((n, m) => n + (m[0] === "NOTE" ? 1.5 : 1), 0);
const H = TOP + BH + 50 + rows * STEP + 40;
let seed = 7, svg = [];
const opt = (o = {}) => ({ seed: seed++, roughness: 1.3, bowing: 1.2, stroke: INK, strokeWidth: 2, ...o });
// extra: SVG attributes added to every path (e.g. a dash pattern, which roughjs paths do not carry)
const draw = (d, extra = "") => gen.toPaths(d).forEach((p) =>
  svg.push(`<path d="${p.d}" stroke="${p.stroke}" stroke-width="${p.strokeWidth}" fill="${p.fill || "none"}" ${extra}/>`));
// Text with a white box behind it, so lifelines never run through a label (box width estimated from the font size)
const text = (x, y, t, size = 22, anchor = "middle", bg = "#ffffff") => {
  const w = t.length * size * 0.52 + 12, h = size * 1.25;
  if (bg) svg.push(`<rect x="${x - w / 2}" y="${y - h / 2}" width="${w}" height="${h}" fill="${bg}"/>`);
  svg.push(`<text x="${x}" y="${y}" font-family="Virgil" font-size="${size}" fill="${INK}" text-anchor="${anchor}" dominant-baseline="middle">${t}</text>`);
};

// Participant boxes and dashed lifelines
for (const [id, label, kind] of P) {
  draw(gen.line(X[id], TOP + BH, X[id], H - 30, opt({ strokeWidth: 1.5, stroke: "#9a9a9a" })), 'stroke-dasharray="10 10"');
  draw(gen.rectangle(X[id] - BW / 2, TOP, BW, BH, opt({ fill: KIND[kind], fillStyle: "hachure", hachureGap: 7, fillWeight: 1.5 })));
  text(X[id], TOP + BH / 2 + 2, label, 24, "middle", null);
}

// Messages, numbered, solid for requests and dashed for replies
let y = TOP + BH + 60, n = 0;
for (const [from, to, label, reply] of M) {
  if (from === "NOTE") {
    const lines = label.split("|"), w = 520, h = 34 * lines.length + 26;
    draw(gen.rectangle(X[to] - w / 2, y - 18, w, h, opt({ fill: KIND.note, fillStyle: "hachure", hachureGap: 8, fillWeight: 1.5 })));
    lines.forEach((l, i) => svg.push(`<text x="${X[to]}" y="${y + 4 + i * 34}" font-family="Virgil" font-size="21" fill="${INK}" stroke="${KIND.note}" stroke-width="8" paint-order="stroke" text-anchor="middle" dominant-baseline="middle">${l}</text>`));
    y += STEP * 1.5;
    continue;
  }
  n += 1;
  const x1 = X[from], x2 = X[to], dir = Math.sign(x2 - x1);
  draw(gen.line(x1, y, x2 - dir * 4, y, opt()), reply ? 'stroke-dasharray="12 9"' : "");
  draw(gen.line(x2 - dir * 4, y, x2 - dir * 20, y - 9, opt()));
  draw(gen.line(x2 - dir * 4, y, x2 - dir * 20, y + 9, opt()));
  text((x1 + x2) / 2 + (label.length > 40 ? 30 : 0), y - 22, label, 21);
  draw(gen.circle(x1, y, 26, opt({ fill: "#ffffff", fillStyle: "solid", strokeWidth: 1.5 })));
  text(x1, y + 1, String(n), 15, "middle", null);
  y += STEP;
}

const html = `<!doctype html><html><head><style>
@font-face { font-family: Virgil; src: url(data:font/woff2;base64,${FONT}) format("woff2"); }
body { margin: 0; background: #fff; }</style></head><body>
<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<rect width="100%" height="100%" fill="#ffffff"/>${svg.join("\n")}</svg></body></html>`;

const browser = await puppeteer.launch({ args: ["--no-sandbox", "--disable-setuid-sandbox"] });
const page = await browser.newPage();
await page.setViewport({ width: Math.ceil(W), height: Math.ceil(H), deviceScaleFactor: 2.5 });
await page.setContent(html);
await page.evaluateHandle("document.fonts.ready");
await page.screenshot({ path: process.argv[2] || "06_sequence_exam_round.png", clip: { x: 0, y: 0, width: W, height: H } });
await browser.close();
console.log("drawn", Math.round(W), "x", Math.round(H));
