"""Export Nyx_Submission.docx to PDF (Word COM on Windows, LibreOffice fallback)."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCX = ROOT / "docs" / "submission" / "NyxViz_作品说明文档.docx"
DEFAULT_PDF = ROOT / "docs" / "submission" / "NyxViz_作品说明文档.pdf"

WD_EXPORT_FORMAT_PDF = 17


def _ps_single_quoted(path: Path) -> str:
    return str(path.resolve()).replace("'", "''")


def export_via_word_com(docx: Path, pdf: Path) -> None:
    docx_s = _ps_single_quoted(docx)
    pdf_s = _ps_single_quoted(pdf)
    script = f"""
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {{
  $doc = $word.Documents.Open('{docx_s}')
  $doc.ExportAsFixedFormat('{pdf_s}', {WD_EXPORT_FORMAT_PDF})
  $doc.Close([ref]0)
}} finally {{
  $word.Quit()
  [void][System.Runtime.Interopservices.Marshal]::ReleaseComObject($word)
}}
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        check=True,
    )


def export_via_pywin32(docx: Path, pdf: Path) -> None:
    import win32com.client  # type: ignore[import-untyped]

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Open(str(docx.resolve()))
    try:
        doc.ExportAsFixedFormat(str(pdf.resolve()), WD_EXPORT_FORMAT_PDF)
    finally:
        doc.Close(False)
        word.Quit()


def export_via_libreoffice(docx: Path, pdf: Path) -> None:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise FileNotFoundError("LibreOffice (soffice) not found on PATH")
    out_dir = pdf.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(docx)],
        check=True,
    )
    produced = out_dir / f"{docx.stem}.pdf"
    if produced != pdf and produced.exists():
        produced.replace(pdf)


def export_pdf(docx: Path, pdf: Path) -> None:
    if not docx.exists():
        raise FileNotFoundError(f"Missing docx: {docx}")
    pdf.parent.mkdir(parents=True, exist_ok=True)
    if pdf.exists():
        pdf.unlink()

    errors: list[str] = []
    if sys.platform == "win32":
        try:
            export_via_word_com(docx, pdf)
            return
        except (subprocess.CalledProcessError, OSError) as exc:
            errors.append(f"Word COM (PowerShell): {exc}")
        try:
            export_via_pywin32(docx, pdf)
            return
        except ImportError:
            pass
        except Exception as exc:
            errors.append(f"Word COM (pywin32): {exc}")

    try:
        export_via_libreoffice(docx, pdf)
        return
    except Exception as exc:
        errors.append(f"LibreOffice: {exc}")

    hint = "Install Microsoft Word (Windows) or LibreOffice, then retry."
    raise RuntimeError("PDF export failed:\n  - " + "\n  - ".join(errors) + f"\n{hint}")


def main() -> int:
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Convert Nyx_Submission.docx to PDF.")
    parser.add_argument("--input", type=Path, default=DEFAULT_DOCX, help="Source .docx")
    parser.add_argument("--output", type=Path, default=DEFAULT_PDF, help="Target .pdf")
    args = parser.parse_args()

    try:
        export_pdf(args.input, args.output)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    size_mb = args.output.stat().st_size / (1024 * 1024)
    print(f"Wrote {args.output} ({size_mb:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
