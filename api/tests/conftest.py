from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_PATHS = (
    ROOT / "core" / "src",
    ROOT / "api" / "src",
)

for src_path in SRC_PATHS:
    src = str(src_path)
    if src not in sys.path:
        sys.path.insert(0, src)
