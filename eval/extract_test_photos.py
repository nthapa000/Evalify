#!/usr/bin/env python3
"""extract_test_photos.py — split the scanned test-sheet PDFs into one named photo per sheet.

    python eval/extract_test_photos.py [src_dir] [out_dir]

Each PDF in src_dir holds one set (2A, 2B, 2C, mcq, omr_L1..L3), one sheet per page in order.
The file name prefix decides the set: "2A_s0x_p1.jpg.pdf" -> 2A_s01_p1.jpg, 2A_s02_p1.jpg, ...
The largest embedded image on each page is the original photo; it is written as-is (no
re-encoding), so the scanner app's small logo strip is dropped.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "test_papers" / "dataset_created"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "test_papers" / "photos"

# Set prefix at the start of the PDF name (omr_L1, mcq, 2A, ...)
SET_RE = re.compile(r"^(omr_L[123]|mcq|2[ABC])_", re.I)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for pdf in sorted(SRC.glob("*.pdf")):
        m = SET_RE.match(pdf.name)
        if not m:
            print(f"skip {pdf.name}: unknown set prefix")
            continue
        prefix = m.group(1)
        doc = fitz.open(pdf)
        # One page = one sheet, numbered in page order
        for i, page in enumerate(doc, start=1):
            infos = page.get_image_info(xrefs=True)
            if not infos:
                print(f"  {pdf.name} page {i}: no image, skipped")
                continue
            # Largest image by pixel count is the photo
            best = max((doc.extract_image(x["xref"]) for x in infos if x["xref"]),
                       key=lambda im: im["width"] * im["height"])
            name = f"{prefix}_s{i:02d}_p1.{best['ext'].replace('jpeg', 'jpg')}"
            (OUT / name).write_bytes(best["image"])
            print(f"  {pdf.name} p{i} -> {name} ({best['width']}x{best['height']})")


if __name__ == "__main__":
    main()
