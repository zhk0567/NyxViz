"""Cross-check docs/report/*.md numeric claims against timeline.json."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from spatial_to_stats import filament_density_band, load_volume_dat

ROOT = Path(__file__).resolve().parents[2]
NYX = ROOT / "Nyx"
STATS = ROOT / "public" / "stats" / "timeline.json"
REPORT = ROOT / "docs" / "report"


def load_timeline() -> dict:
    return json.loads(STATS.read_text(encoding="utf-8"))


def check_task1(text: str, steps: dict[int, dict]) -> list[str]:
    issues: list[str] = []
    for t in [0, 25, 50, 75, 99]:
        m = re.search(
            rf"t={t}: mean=([\d.]+), σ=([\d.]+), p99=([\d.]+), max=([\d.]+)",
            text,
        )
        if not m:
            issues.append(f"task1: missing stats line for t={t}")
            continue
        s = steps[t]
        exp = [s["mean"], s["std"], s["p99"], s["max"]]
        for i, (got_s, exp_v) in enumerate(zip(m.groups(), exp, strict=True)):
            if abs(float(got_s) - exp_v) > 1e-3:
                issues.append(f"task1 t={t} field[{i}]: report={got_s} timeline={exp_v:.4f}")
    return issues


def check_task2(text: str, s0: dict, s99: dict) -> list[str]:
    issues: list[str] = []
    span0 = s0["p99"] - s0["p01"]
    span99 = s99["p99"] - s99["p01"]
    pct = (span99 - span0) / span0 * 100
    m = re.search(r"p99−p01\*\* 由 ([\d.]+) 增至 ([\d.]+)（\+([\d.]+)%）", text)
    if not m:
        issues.append("task2: span line not found")
    else:
        if abs(float(m.group(1)) - span0) > 0.01:
            issues.append(f"task2 span0: {m.group(1)} vs {span0:.3f}")
        if abs(float(m.group(2)) - span99) > 0.01:
            issues.append(f"task2 span99: {m.group(2)} vs {span99:.3f}")
        if abs(float(m.group(3)) - pct) > 0.2:
            issues.append(f"task2 span pct: {m.group(3)} vs {pct:.1f}")
    m = re.search(r"σ\*\* 由 ([\d.]+) 升至 ([\d.]+)", text)
    if not m:
        issues.append("task2: std line not found")
    elif abs(float(m.group(1)) - s0["std"]) > 1e-3 or abs(float(m.group(2)) - s99["std"]) > 1e-3:
        issues.append("task2: std mismatch with timeline")
    tail = s99["tailMassAboveP99"] * 100
    m = re.search(r"体积占比\*\*约 ([\d.]+)%", text)
    if m and abs(float(m.group(1)) - tail) > 0.05:
        issues.append(f"task2 tail mass: {m.group(1)} vs {tail:.2f}")
    return issues


def check_task3(text: str, timeline: dict, s0: dict, s99: dict) -> list[str]:
    issues: list[str] = []
    gmin, gmax = timeline["globalMin"], timeline["globalMax"]
    bc = timeline["binCount"]
    if f"[{gmin:.4f}, {gmax:.4f}]" not in text:
        issues.append("task3: global bin bounds mismatch")
    if f"{bc} bins" not in text:
        issues.append("task3: bin count mismatch")
    if f"{s0['std']:.4f}" not in text or f"{s99['std']:.4f}" not in text:
        issues.append("task3: std range mismatch")
    if f"{s0['skewness']:.4f}" not in text or f"{s99['skewness']:.4f}" not in text:
        issues.append("task3: skewness mismatch")
    return issues


def check_task4(text: str, s99: dict) -> list[str]:
    issues: list[str] = []
    if f"p99={s99['p99']:.4f}" not in text:
        issues.append("task4: p99 mismatch")
    if f"p01={s99['p01']:.4f}" not in text:
        issues.append("task4: p01 mismatch")
    vol_path = NYX / "0099.dat"
    if vol_path.exists():
        lo, hi, _ = filament_density_band(load_volume_dat(vol_path))
        if f"ρ∈[{lo:.2f}, {hi:.2f}]" not in text:
            issues.append("task4: filament band mismatch")
    return issues


def main() -> int:
    if not STATS.exists():
        print("Missing timeline.json — run: npm run precompute", file=sys.stderr)
        return 1

    timeline = load_timeline()
    steps = {s["timestep"]: s for s in timeline["timesteps"]}
    s0, s99 = steps[0], steps[99]

    all_issues: list[str] = []
    all_issues.extend(check_task1((REPORT / "task1_volume.md").read_text(encoding="utf-8"), steps))
    all_issues.extend(
        check_task2((REPORT / "task2_evolution.md").read_text(encoding="utf-8"), s0, s99)
    )
    all_issues.extend(
        check_task3(
            (REPORT / "task3_histogram.md").read_text(encoding="utf-8"),
            timeline,
            s0,
            s99,
        )
    )
    all_issues.extend(
        check_task4((REPORT / "task4_brush.md").read_text(encoding="utf-8"), s99)
    )

    if all_issues:
        print("Report vs timeline.json — FAILED:", file=sys.stderr)
        for issue in all_issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1

    print(
        f"Report stats OK — {len(steps)} timesteps, "
        f"global [{timeline['globalMin']:.4f}, {timeline['globalMax']:.4f}]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
