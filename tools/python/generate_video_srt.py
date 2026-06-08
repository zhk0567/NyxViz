#!/usr/bin/env python3
"""从 VIDEO_NARRATION_TTS.txt 生成 PR 字幕（与 TTS 正文统一，一句一条，无标点）。"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TTS = ROOT / "docs" / "competition" / "VIDEO_NARRATION_TTS.txt"
OUT = ROOT / "docs" / "competition" / "VIDEO_NARRATION.srt"

# 7 段正文对应分镜时段（秒）— 与 VIDEO_NARRATION.md 分镜表同步
# 开篇 | 任务一 | 任务二 | 任务三 | 任务四 | 发现卡+结语（约 5:00 旁白 + 停顿）
SECTION_ENDS = [25.0, 70.0, 110.0, 140.0, 255.0, 270.0, 285.0]

MIN_CUE_SEC = 1.6
MAX_CUE_CHARS = 32

STRIP_PUNCT = set("。？！·""''「」:!?'\"[]{}")
SPACE_PUNCT = set("，、,;；…—－–—:：（）()")


def strip_punctuation(text: str) -> str:
    out: list[str] = []
    for c in text:
        if c in SPACE_PUNCT:
            out.append(" ")
        elif c in STRIP_PUNCT:
            continue
        else:
            out.append(c)
    return " ".join("".join(out).split())


def load_tts_paragraphs(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    in_body = False
    paragraphs: list[str] = []
    buf: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == "正文":
            in_body = True
            continue
        if not in_body:
            continue
        if stripped.startswith("----"):
            if buf:
                paragraphs.append("".join(buf).strip())
                buf = []
            if paragraphs:
                break
            continue
        if not stripped:
            if buf:
                paragraphs.append("".join(buf).strip())
                buf = []
            continue
        buf.append(stripped)
    if buf:
        paragraphs.append("".join(buf).strip())
    return paragraphs


def force_split(seg: str, max_chars: int) -> list[str]:
    """无逗号的超长句按字数硬切，避免 PR 自动换行。"""
    seg = seg.strip()
    if len(strip_punctuation(seg)) <= max_chars:
        return [seg]
    parts: list[str] = []
    rest = seg
    while rest:
        if len(strip_punctuation(rest)) <= max_chars:
            parts.append(rest)
            break
        cut = 1
        while cut <= len(rest) and len(strip_punctuation(rest[:cut])) <= max_chars:
            cut += 1
        cut -= 1
        if cut <= 0:
            cut = 1
        parts.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    return parts


def split_for_subtitles(text: str, max_chars: int = MAX_CUE_CHARS) -> list[str]:
    """先按句号/分号切句，过长再按逗号切，仍过长则按字数切。"""
    segments: list[str] = []
    for seg in re.split(r"[。；]", text):
        seg = seg.strip()
        if seg:
            segments.append(seg)

    result: list[str] = []
    for seg in segments:
        if len(strip_punctuation(seg)) <= max_chars:
            result.append(seg)
            continue
        clauses = [c.strip() for c in seg.split("，") if c.strip()]
        buf = ""
        for cl in clauses:
            trial = f"{buf}，{cl}" if buf else cl
            if len(strip_punctuation(trial)) <= max_chars or not buf:
                buf = trial
            else:
                result.extend(force_split(buf, max_chars))
                buf = cl
        if buf:
            if len(strip_punctuation(buf)) <= max_chars:
                result.append(buf)
            else:
                result.extend(force_split(buf, max_chars))
    final: list[str] = []
    for seg in result:
        final.extend(force_split(seg, max_chars))
    return final


def fmt_ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    if ms >= 1000:
        ms = 0
        s += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def section_to_cues(start: float, end: float, sentences: list[str]) -> list[tuple[float, float, str]]:
    span = end - start
    if not sentences:
        return []
    weights = [max(len(strip_punctuation(s)), 1) for s in sentences]
    total = sum(weights)
    raw = [span * w / total for w in weights]
    boosted = [max(d, MIN_CUE_SEC) for d in raw]
    scale = span / sum(boosted)
    durations = [d * scale for d in boosted]
    cues: list[tuple[float, float, str]] = []
    t = start
    for sent, dur in zip(sentences, durations):
        cues.append((t, t + dur, sent))
        t += dur
    s0, _, text = cues[-1]
    cues[-1] = (s0, end, text)
    return cues


def build_cues(paragraphs: list[str]) -> list[tuple[float, float, str]]:
    if len(paragraphs) != len(SECTION_ENDS):
        raise ValueError(
            f"TTS 正文应为 {len(SECTION_ENDS)} 段，实际 {len(paragraphs)} 段。"
            "请检查 VIDEO_NARRATION_TTS.txt。"
        )
    all_cues: list[tuple[float, float, str]] = []
    start = 0.0
    for end, para in zip(SECTION_ENDS, paragraphs):
        sentences = split_for_subtitles(para)
        all_cues.extend(section_to_cues(start, end, sentences))
        start = end
    return all_cues


def build_srt(cues: list[tuple[float, float, str]]) -> str:
    blocks: list[str] = []
    for i, (start, end, text) in enumerate(cues, 1):
        blocks.append(f"{i}\n{fmt_ts(start)} --> {fmt_ts(end)}\n{strip_punctuation(text)}\n")
    return "\n".join(blocks)


def main() -> None:
    paragraphs = load_tts_paragraphs(TTS)
    cues = build_cues(paragraphs)
    OUT.write_text(build_srt(cues), encoding="utf-8-sig")
    stripped = [strip_punctuation(c[2]) for c in cues]
    max_len = max(len(s) for s in stripped)
    print(f"Source: {TTS.name} ({len(paragraphs)} paragraphs)")
    print(f"Wrote {OUT} ({len(cues)} cues, ~{cues[-1][1]:.0f}s, max {max_len} chars/cue)")


if __name__ == "__main__":
    main()
