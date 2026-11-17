// sketch_lib.mjs — tiny helpers to draw diagrams in the Excalidraw style: roughjs strokes (the library Excalidraw
// uses) and the Virgil handwriting font, rendered to PNG with a headless browser.
import fs from "node:fs";
import rough from "roughjs/bundled/rough.esm.js";
import puppeteer from "puppeteer";

export const INK = "#1e1e1e";
// Same colour key as the other diagrams: people grey, application blue, data yellow, AI models green
export const FILL = { person: "#c9c2b6", app: "#8fb8de", data: "#f5d97a", model: "#94c99a", note: "#f5d97a" };
// Lighter colours for flat (unshaded) boxes
export const FLAT = { person: "#ebe7e0", app: "#dbe8f5", data: "#fbefc6", model: "#dcefdd", note: "#fbefc6" };

// A drawing surface of W x H; every helper appends SVG to it
// style.flat: boxes filled with one light colour instead of hachure shading
export function canvas(W, H, style = {}) {
  const gen = rough.generator();
  const svg = [];
  let seed = 11;
  const opt = (o = {}) => ({ seed: seed++, roughness: 1.3, bowing: 1.2, stroke: INK, strokeWidth: 2, ...o });
  // extra: SVG attributes for every path (roughjs paths do not carry a dash pattern)
  const draw = (d, extra = "") => gen.toPaths(d).forEach((p) =>
    svg.push(`<path d="${p.d}" stroke="${p.stroke}" stroke-width="${p.strokeWidth}" fill="${p.fill || "none"}" ${extra}/>`));

  // Text centred at (x, y); "|" splits lines; bg draws a box behind it so lines never run through a label
  const text = (x, y, t, size = 21, bg = null) => {
    const lines = String(t).split("|"), lh = size * 1.35;
    lines.forEach((l, i) => {
      const ly = y + (i - (lines.length - 1) / 2) * lh;
      if (bg) {
        const w = l.length * size * 0.52 + 12;
        svg.push(`<rect x="${x - w / 2}" y="${ly - lh / 2}" width="${w}" height="${lh}" fill="${bg}"/>`);
      }
      svg.push(`<text x="${x}" y="${ly}" font-family="Virgil" font-size="${size}" fill="${INK}" text-anchor="middle" dominant-baseline="middle">${l}</text>`);
    });
  };
  // Hachure-filled box with a label (kind = a FILL key)
  const fillOf = (kind) => style.flat ? { fill: FLAT[kind], fillStyle: "solid" }
    : { fill: FILL[kind], fillStyle: "hachure", hachureGap: 7, fillWeight: 1.5 };
  const box = (x, y, w, h, label, kind = "app", size = 21) => {
    draw(gen.rectangle(x, y, w, h, opt(fillOf(kind))));
    text(x + w / 2, y + h / 2 + 1, label, size);
  };
  // Arrow from (x1,y1) to (x2,y2) with an open head; dashed for replies
  const arrow = (x1, y1, x2, y2, { dashed = false, label = "", size = 19, labelDy = -20 } = {}) => {
    const a = Math.atan2(y2 - y1, x2 - x1), hx = (s) => x2 - 16 * Math.cos(a + s), hy = (s) => y2 - 16 * Math.sin(a + s);
    draw(gen.line(x1, y1, x2, y2, opt()), dashed ? 'stroke-dasharray="12 9"' : "");
    draw(gen.line(x2, y2, hx(0.45), hy(0.45), opt()));
    draw(gen.line(x2, y2, hx(-0.45), hy(-0.45), opt()));
    if (label) text((x1 + x2) / 2, (y1 + y2) / 2 + labelDy, label, size, "#ffffff");
  };
  const line = (x1, y1, x2, y2, extra = "", o = {}) => draw(gen.line(x1, y1, x2, y2, opt(o)), extra);
  // Numbered step marker
  const step = (x, y, n) => {
    draw(gen.circle(x, y, 26, opt({ fill: "#ffffff", fillStyle: "solid", strokeWidth: 1.5 })));
    text(x, y + 1, String(n), 15);
  };
  // Dashed frame with a title tab (loops, groups)
  const frame = (x, y, w, h, title) => {
    draw(gen.rectangle(x, y, w, h, opt({ strokeWidth: 1.5, stroke: "#6b6b6b" })), 'stroke-dasharray="8 7"');
    text(x + title.length * 5.5 + 18, y + 18, title, 18, "#ffffff");
  };
  return { W, H, svg, draw, text, box, arrow, line, step, frame, gen, opt, fillOf };
}

// Render the canvas to a PNG file (2.5x for print quality)
export async function render(c, out) {
  const font = fs.readFileSync(process.env.VIRGIL_FONT || "Virgil.woff2").toString("base64");
  const html = `<!doctype html><html><head><style>
@font-face { font-family: Virgil; src: url(data:font/woff2;base64,${font}) format("woff2"); }
body { margin: 0; background: #fff; }</style></head><body>
<svg xmlns="http://www.w3.org/2000/svg" width="${c.W}" height="${c.H}"><rect width="100%" height="100%" fill="#fff"/>
${c.svg.join("\n")}</svg></body></html>`;
  const browser = await puppeteer.launch({ args: ["--no-sandbox", "--disable-setuid-sandbox"] });
  const page = await browser.newPage();
  await page.setViewport({ width: Math.ceil(c.W), height: Math.ceil(c.H), deviceScaleFactor: 2.5 });
  await page.setContent(html);
  await page.evaluateHandle("document.fonts.ready");
  await page.screenshot({ path: out, clip: { x: 0, y: 0, width: c.W, height: c.H } });
  await browser.close();
}
