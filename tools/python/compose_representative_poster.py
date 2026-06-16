"""Compose representative poster: 4-act narrative science story → 3840×5200."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_figures import (  # noqa: E402
    STATS,
    compose_representative_poster,
    representative_poster,
)


def main() -> int:
    timeline = json.loads(STATS.read_text(encoding="utf-8"))
    compose_representative_poster(timeline)
    representative_poster(timeline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
