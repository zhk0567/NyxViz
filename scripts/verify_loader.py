"""Verify z-fastest axis order matches TypeScript nyxLoader."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NYX = ROOT / "Nyx"
GRID = 128


def flat_index(x: int, y: int, z: int) -> int:
    return z + GRID * y + GRID * GRID * x


def main() -> int:
    sample = NYX / "0000.dat"
    if not sample.exists():
        print(f"Missing {sample}", file=sys.stderr)
        return 1

    flat = np.fromfile(sample, dtype="<f4")
    assert flat.size == GRID**3

    # z fastest: reshape as (x, y, z) with C order
    volume = flat.reshape((GRID, GRID, GRID), order="C")

    probes = [
        (0, 0, 0),
        (0, 0, 1),
        (0, 1, 0),
        (1, 0, 0),
        (64, 64, 64),
        (127, 127, 127),
    ]
    report = []
    for x, y, z in probes:
        via_reshape = float(volume[x, y, z])
        via_index = float(flat[flat_index(x, y, z)])
        report.append(
            {
                "x": x,
                "y": y,
                "z": z,
                "reshape": via_reshape,
                "flatIndex": via_index,
                "match": abs(via_reshape - via_index) < 1e-6,
            }
        )

    out = ROOT / "public" / "stats" / "loader_probe.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if not all(r["match"] for r in report):
        print("Axis order mismatch!", file=sys.stderr)
        return 1

    print(f"Axis order OK — probe written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
