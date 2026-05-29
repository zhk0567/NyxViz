"""Count answer-sheet characters for docs/report/task*.md (ChinaVis ≤800 字/题)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "report"

TASK_FILES: list[tuple[str, str]] = [
    ("任务一", "task1_volume.md"),
    ("任务二", "task2_evolution.md"),
    ("任务三", "task3_histogram.md"),
    ("任务四", "task4_brush.md"),
]

FIGURES_HEADING = re.compile(r"^##\s+配图")
TOOLS_HEADING = re.compile(r"^##\s+工具与环境")
SECTION_HEADING = re.compile(r"^##\s+")
IMAGE_LINE = re.compile(r"^!\[")
HEADING = re.compile(r"^(#+)\s+(.*)$")
BOLD = re.compile(r"\*\*(.+?)\*\*")
CODE = re.compile(r"`([^`]+)`")
LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def strip_markdown_for_answer(md: str, *, exclude_tools: bool = False) -> str:
    """Text likely pasted into the official answer sheet (no figure blocks)."""
    lines: list[str] = []
    skip = False
    for raw in md.splitlines():
        line = raw.rstrip()
        if FIGURES_HEADING.match(line) or (exclude_tools and TOOLS_HEADING.match(line)):
            skip = True
            continue
        if SECTION_HEADING.match(line):
            skip = False
        if skip or IMAGE_LINE.match(line.strip()):
            continue
        m = HEADING.match(line)
        if m:
            line = m.group(2)
        line = BOLD.sub(r"\1", line)
        line = CODE.sub(r"\1", line)
        line = LINK.sub(r"\1", line)
        if line.strip():
            lines.append(line.strip())
    return "\n".join(lines)


def count_chars(text: str) -> int:
    """Non-whitespace characters (Chinese + punctuation + digits + Latin)."""
    return len(re.sub(r"\s+", "", text))


def count_cjk(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def analyze_file(path: Path, *, exclude_tools: bool) -> dict[str, int | str]:
    raw = path.read_text(encoding="utf-8")
    body = strip_markdown_for_answer(raw, exclude_tools=exclude_tools)
    return {
        "path": path.name,
        "raw_chars": count_chars(raw),
        "answer_chars": count_chars(body),
        "cjk": count_cjk(body),
        "body_preview_lines": len(body.splitlines()),
    }


def main() -> int:
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Count report chars for answer-sheet paste (≤800/题).")
    parser.add_argument("--limit", type=int, default=800, help="Max chars per task (default: 800)")
    parser.add_argument(
        "--exclude-tools",
        action="store_true",
        help="Only count body without ## 工具与环境 (typical paste into answer sheet)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any task exceeds --limit (uses paste count unless --exclude-tools is off)",
    )
    args = parser.parse_args()

    if not REPORT.is_dir():
        print(f"Missing {REPORT}", file=sys.stderr)
        return 1

    failures: list[str] = []
    rows: list[tuple[str, str, int, int]] = []

    for label, name in TASK_FILES:
        path = REPORT / name
        if not path.exists():
            rows.append((label, name, -1, -1))
            failures.append(f"{name}: file missing")
            continue
        with_tools = int(analyze_file(path, exclude_tools=False)["answer_chars"])
        paste = int(analyze_file(path, exclude_tools=True)["answer_chars"])
        if paste > args.limit:
            failures.append(f"{name}: paste={paste}, full={with_tools} (limit {args.limit})")
        rows.append((label, name, with_tools, paste))

    if args.exclude_tools:
        print(f"答卷正文字数（去配图、去工具段，非空白计字）· 上限 {args.limit} 字/题\n")
        print(f"{'任务':<8} {'文件':<22} {'粘贴字数':>8} {'状态':>6}")
        print("-" * 48)
        total = 0
        for label, name, full, paste in rows:
            if paste < 0:
                print(f"{label:<8} {name:<22} {'—':>8}  缺失")
                continue
            total += paste
            status = "OK" if paste <= args.limit else "超限"
            print(f"{label:<8} {name:<22} {paste:>8} {status:>6}")
        print("-" * 48)
        print(f"{'合计':<8} {'四题粘贴正文':<22} {total:>8}")
    else:
        print(f"答卷正文字数（去配图，非空白计字）· 上限 {args.limit} 字/题\n")
        print(f"{'任务':<8} {'文件':<22} {'含工具段':>8} {'粘贴用':>8} {'状态':>6}")
        print("-" * 56)
        total_full = total_paste = 0
        for label, name, full, paste in rows:
            if full < 0:
                print(f"{label:<8} {name:<22} {'—':>8} {'—':>8}  缺失")
                continue
            total_full += full
            total_paste += paste
            status = "OK" if paste <= args.limit else "超限"
            print(f"{label:<8} {name:<22} {full:>8} {paste:>8} {status:>6}")
        print("-" * 56)
        print(f"{'合计':<8} {'四题正文':<22} {total_full:>8} {total_paste:>8}")

    print()
    print("说明：「粘贴用」= 再去掉各题 ## 工具与环境；官方答卷框通常只粘贴该部分。")

    if failures:
        print("\n需压缩或删减的条目：", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        if args.strict:
            return 1
    elif args.strict or args.exclude_tools:
        print("\n四题均在字数上限内（粘贴用计数）。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
