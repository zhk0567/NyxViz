"""Fill official 1-II_answerSheet.docx from docs/report and docs/figures."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.shared import Cm, Pt
from docx.text.paragraph import Paragraph

from count_report_chars import count_chars, strip_markdown_for_answer
from report_docx_shared import REPORT, ROOT, TASK_MD, resolve_task_images

ANSWER_MARKER = "（下面是答题区域）"
QUESTION_START = re.compile(r"^\d、")
TEMPLATE_CANDIDATES = [
    ROOT / "docs" / "competition" / "1-II_answerSheet.docx",
    ROOT / "1-II_answerSheet.docx",
]
TEAM_CONFIG = ROOT / "docs" / "competition" / "team.json"
TEAM_CONFIG_EXAMPLE = ROOT / "docs" / "competition" / "team.json.example"
DEFAULT_OUT = ROOT / "docs" / "submission" / "Nyx_answerSheet_filled.docx"
CHAR_LIMIT = 800


def find_template() -> Path:
    for p in TEMPLATE_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError(
        "Missing 1-II_answerSheet.docx — download to docs/competition/:\n"
        "  https://chinavis.org/2026/challenge/1-II_answerSheet.docx"
    )


def insert_paragraph_after(paragraph: Paragraph) -> Paragraph:
    new_p = OxmlElement("w:p")
    paragraph._element.addnext(new_p)
    return Paragraph(new_p, paragraph._parent)


def remove_paragraphs_between(doc: Document, start_exclusive: int, end_exclusive: int) -> None:
    if end_exclusive <= start_exclusive + 1:
        return
    elements = [doc.paragraphs[j]._element for j in range(start_exclusive + 1, end_exclusive)]
    for el in elements:
        el.getparent().remove(el)


def marker_indices(doc: Document) -> list[int]:
    return [i for i, p in enumerate(doc.paragraphs) if ANSWER_MARKER in p.text]


def next_question_index(doc: Document, after: int) -> int:
    for j in range(after + 1, len(doc.paragraphs)):
        if QUESTION_START.match(doc.paragraphs[j].text.strip()):
            return j
    return len(doc.paragraphs)


def body_lines(md_path: Path) -> list[str]:
    text = strip_markdown_for_answer(md_path.read_text(encoding="utf-8"), exclude_tools=True)
    return [ln for ln in text.splitlines() if ln.strip()]


def append_line_after(anchor: Paragraph, line: str, *, bullet: bool = False, bold: bool = False) -> Paragraph:
    para = insert_paragraph_after(anchor)
    text = f"• {line}" if bullet else line
    run = para.add_run(text)
    run.bold = bold
    return para


def fill_answer_region(
    doc: Document,
    task_index: int,
    md_name: str,
    *,
    char_limit: int,
) -> tuple[int, int]:
    markers = marker_indices(doc)
    if task_index >= len(markers):
        raise IndexError(f"Task {task_index + 1}: answer marker not found in template")
    marker_idx = markers[task_index]
    end_idx = next_question_index(doc, marker_idx)
    remove_paragraphs_between(doc, marker_idx, end_idx)

    md_path = REPORT / md_name
    lines = body_lines(md_path)
    body_text = "".join(lines)
    n_chars = count_chars(body_text)

    marker_para = doc.paragraphs[marker_idx]
    anchor = marker_para

    note = f"（自动填入，正文 {n_chars} 字"
    if n_chars > char_limit:
        note += f"，超出建议上限 {char_limit} 字，提交前请删减"
    note += "）"
    anchor = append_line_after(anchor, note)

    for line in lines:
        if line.startswith("- "):
            anchor = append_line_after(anchor, line[2:], bullet=True)
        elif line.endswith("：") or (len(line) < 48 and "：" in line and not line[0].isdigit()):
            anchor = append_line_after(anchor, line, bold=True)
        else:
            anchor = append_line_after(anchor, line)

    for img_path in resolve_task_images(md_name):
        anchor = append_line_after(anchor, f"图：{img_path.stem}")
        pic_para = insert_paragraph_after(anchor)
        pic_para.add_run().add_picture(str(img_path), width=Cm(14))
        anchor = pic_para

    return n_chars, len(resolve_task_images(md_name))


def apply_team_config(doc: Document, config: dict) -> None:
    mapping = [
        ("team_name", "参赛队名称："),
        ("member_line_1", "团队成员："),
        ("tools", "使用的分析工具或开发工具"),
        ("person_days", "共计耗费时间"),
        ("publish_ok", "本次比赛结束后"),
        ("consistent_with_registration", "团队成员是否与报名表一致"),
        ("student_team", "是否学生队"),
    ]
    for key, prefix in mapping:
        value = config.get(key)
        if not value:
            continue
        for para in doc.paragraphs:
            if para.text.strip().startswith(prefix):
                para.text = f"{prefix}{value}"
                break

    extra_members = config.get("member_lines_extra")
    if extra_members:
        for i, para in enumerate(doc.paragraphs):
            if para.text.strip().startswith("团队成员："):
                if i + 1 < len(doc.paragraphs) and not QUESTION_START.match(
                    doc.paragraphs[i + 1].text.strip()
                ):
                    doc.paragraphs[i + 1].text = extra_members[0] if isinstance(extra_members, list) else extra_members
                break


def fill_answer_sheet(
    template: Path,
    output: Path,
    *,
    team_config: Path | None = None,
    char_limit: int = CHAR_LIMIT,
) -> list[tuple[str, int, int]]:
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template, output)
    doc = Document(str(output))

    style = doc.styles["Normal"]
    style.font.name = "宋体"
    style.font.size = Pt(11)

    cfg_path = team_config or TEAM_CONFIG
    if cfg_path.exists():
        config = json.loads(cfg_path.read_text(encoding="utf-8"))
        apply_team_config(doc, config)
        print(f"Applied team config: {cfg_path}")

    stats: list[tuple[str, int, int]] = []
    for i, md_name in enumerate(TASK_MD):
        chars, n_img = fill_answer_region(doc, i, md_name, char_limit=char_limit)
        stats.append((md_name, chars, n_img))

    doc.save(output)
    return stats


def main() -> int:
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Fill ChinaVis 1-II answer sheet from NyxViz report.")
    parser.add_argument("--template", type=Path, default=None, help="Source answerSheet.docx")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT, help="Filled output path")
    parser.add_argument("--team-config", type=Path, default=None, help="team.json with 参赛队信息")
    parser.add_argument("--limit", type=int, default=CHAR_LIMIT, help="Char limit warning per task")
    args = parser.parse_args()

    try:
        template = args.template or find_template()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    if not REPORT.exists():
        print(f"Missing {REPORT} — run: npm run export-report", file=sys.stderr)
        return 1

    try:
        stats = fill_answer_sheet(
            template,
            args.output,
            team_config=args.team_config,
            char_limit=args.limit,
        )
    except Exception as exc:
        print(f"Fill failed: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {args.output}\n")
    print(f"{'任务':<12} {'字数':>6} {'图':>4}  状态")
    over = 0
    for md_name, chars, n_img in stats:
        status = "OK" if chars <= args.limit else "超限"
        if chars > args.limit:
            over += 1
        print(f"{md_name:<12} {chars:>6} {n_img:>4}  {status}")
    if over:
        print(f"\n{over} 题超出 {args.limit} 字 — 可编辑 team.json 后重跑，或在 Word 中删减。", file=sys.stderr)
    if not TEAM_CONFIG.exists() and TEAM_CONFIG_EXAMPLE.exists():
        print(f"\n提示：复制 {TEAM_CONFIG_EXAMPLE.name} → team.json 填写队名/成员/工具栈后重跑。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
