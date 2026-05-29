"""Build submission assets: figures, report, docx, representative JPG."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "submission"
PY = ROOT / "tools" / "python"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True, shell=sys.platform == "win32")


def main() -> int:
    run([sys.executable, str(PY / "precompute.py")])
    run([sys.executable, str(PY / "generate_figures.py")])
    run([sys.executable, str(PY / "export_report.py")])
    run([sys.executable, str(PY / "export_docx.py")])

    OUT.mkdir(parents=True, exist_ok=True)
    rep = OUT / "submission_representative.jpg"
    if rep.exists():
        print(f"Representative image: {rep}")
    else:
        print("Warning: submission_representative.jpg missing — run generate_figures.py", file=sys.stderr)

    docx = ROOT / "docs" / "report" / "Nyx_Submission.docx"
    if docx.exists():
        import shutil

        shutil.copy2(docx, OUT / "Nyx_Submission.docx")
        print(f"Copied {OUT / 'Nyx_Submission.docx'}")

    print("\nSubmission pack ready under docs/submission/")
    print("  - Nyx_Submission.docx  (paste into official answer sheet)")
    print("  - submission_representative.jpg")
    print("  - Full figures: docs/figures/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
