"""Replace embedded figure PNGs in an existing docx (preserve text/layout)."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from docx import Document

from report_docx_shared import ROOT, resolve_image
from work_doc_content import Figure, build_blocks

STATS = ROOT / "public" / "stats" / "timeline.json"
DEFAULT_DOCX = ROOT / "docs" / "submission" / "NyxViz_作品说明文档.docx"

BLIP = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"
EMBED = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
INLINE = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline"


def load_timeline() -> dict:
    return json.loads(STATS.read_text(encoding="utf-8"))


def unique_figure_files(timeline: dict) -> list[str]:
    seen: set[str] = set()
    files: list[str] = []
    for block in build_blocks(timeline):
        if isinstance(block, Figure) and block.file not in seen:
            seen.add(block.file)
            files.append(block.file)
    return files


def iter_embedded_image_parts(doc: Document):
    for inline in doc.element.body.iter(INLINE):
        blip = inline.find(f".//{BLIP}")
        if blip is None:
            continue
        rid = blip.get(EMBED)
        if not rid:
            continue
        part = doc.part.related_parts.get(rid)
        if part is not None:
            yield part


def replace_figures(docx_path: Path, timeline: dict, *, dry_run: bool = False) -> int:
    fig_files = unique_figure_files(timeline)
    doc = Document(docx_path)
    parts = list(iter_embedded_image_parts(doc))

    if len(parts) != len(fig_files):
        print(
            f"Warning: docx has {len(parts)} embedded images, "
            f"expected {len(fig_files)} unique figures from build_blocks.",
            file=sys.stderr,
        )

    n = min(len(parts), len(fig_files))
    replaced = 0
    for i in range(n):
        name = fig_files[i]
        src = resolve_image(name)
        if not src:
            print(f"Skip missing figure file: {name}", file=sys.stderr)
            continue
        blob = src.read_bytes()
        if dry_run:
            print(f"Would replace image #{i + 1} with {name} ({len(blob)} bytes)")
        else:
            parts[i]._blob = blob  # type: ignore[attr-defined]
            replaced += 1
            print(f"Replaced image #{i + 1} ← {name}")

    if not dry_run and replaced:
        doc.save(docx_path)
    return replaced


def main() -> int:
    parser = argparse.ArgumentParser(description="Swap docx embedded PNGs from docs/figures/")
    parser.add_argument("--docx", type=Path, default=DEFAULT_DOCX)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backup", action="store_true", help="Copy docx before replace")
    args = parser.parse_args()

    if not STATS.exists():
        print("Missing timeline.json — run: npm run precompute", file=sys.stderr)
        return 1
    if not args.docx.is_file():
        print(f"Missing docx: {args.docx}", file=sys.stderr)
        return 1

    if args.backup and not args.dry_run:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = args.docx.with_name(f"{args.docx.stem}.backup-{stamp}{args.docx.suffix}")
        shutil.copy2(args.docx, backup)
        print(f"Backup: {backup}")

    timeline = load_timeline()
    n = replace_figures(args.docx, timeline, dry_run=args.dry_run)
    if args.dry_run:
        print(f"Dry run complete ({n} would be replaced).")
    else:
        print(f"Updated {args.docx} ({n} images replaced).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
