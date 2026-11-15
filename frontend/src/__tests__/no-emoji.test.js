// no-emoji.test.js — the UI must not use emoji or pictographic symbols (user rule, 15 Nov).
import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

// Emoji, dingbats (✓ ✕ ★ ✔ ✘ …), misc symbols and the emoji variation selector
const PICTO = /[\p{Extended_Pictographic}☀-➿⭐️]/u;

// Every .js/.jsx file under src/, except tests (which may name the old symbols)
function sources(dir) {
  return readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) return f === "__tests__" || f === "test" ? [] : sources(p);
    return /\.(jsx?|css)$/.test(f) ? [p] : [];
  });
}

describe("no emoji in the UI", () => {
  // Why: the user asked for no emoji anywhere in the frontend; this keeps them from coming back
  it("has no pictographic characters in any source file", () => {
    const hits = [];
    for (const file of sources(join(__dirname, ".."))) {
      readFileSync(file, "utf8").split("\n").forEach((line, i) => {
        if (PICTO.test(line)) hits.push(`${file.split("/src/")[1]}:${i + 1}: ${line.trim().slice(0, 60)}`);
      });
    }
    expect(hits).toEqual([]);
  });
});
