from __future__ import annotations

import sys
from pathlib import Path

CLI_ROOT = Path(__file__).resolve().parents[1]
CLI_SRC = CLI_ROOT / "src"
CORE_SRC = CLI_ROOT.parent / "core" / "src"

for src in (CLI_SRC, CORE_SRC):
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
