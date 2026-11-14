# dataset.py — load a labelled sheet set (format documented in eval/README.md).

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional


@dataclass
class Sheet:
    """One student answer sheet with its gold labels."""
    sheet_id: str
    split: str                       # dev | test
    paper: dict                      # same shape as a MongoDB paper document
    sheet_type: str                  # omr | handwritten
    pages: List[str]                 # absolute image paths
    gold: Dict[str, dict]            # question id → {answer | transcript, marks, concepts, planted_errors, crop}
    root: Path = field(default=Path("."))

    def crop_box(self, qid: str) -> Optional[dict]:
        """Optional gold crop {"page": i, "bbox": [x0, y0, x1, y1] (0–1000)} for a question."""
        return self.gold.get(qid, {}).get("crop")


def load(set_dir: str, split: Optional[str] = None) -> Iterator[Sheet]:
    """Yield sheets from <set_dir>/manifest.jsonl, optionally only one split."""
    root = Path(set_dir).resolve()
    papers: Dict[str, dict] = {}
    for line in (root / "manifest.jsonl").read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        row = json.loads(line)
        if split and row.get("split") != split:
            continue
        # Papers are shared between sheets; load each JSON once
        p = row["paper"]
        if p not in papers:
            papers[p] = json.loads((root / p).read_text())
        yield Sheet(row["sheet_id"], row.get("split", "dev"), papers[p], row.get("sheet_type", "handwritten"),
                    [str(root / x) for x in row["pages"]], row.get("gold", {}), root)
