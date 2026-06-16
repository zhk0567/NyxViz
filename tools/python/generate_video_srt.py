#!/usr/bin/env python3
"""从 VIDEO_NARRATION_TTS.txt 生成 PR 字幕（与 TTS 正文统一，一句一条，无标点）。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TTS = ROOT / "docs" / "competition" / "VIDEO_NARRATION_TTS.txt"
OUT = ROOT / "docs" / "competition" / "VIDEO_NARRATION.srt"

# 11 行正文对应 11 个 scene（一行一页）— 与 VIDEO_SCRIPT.md §2、VIDEO_NARRATION_TTS.txt 同步
# 行 | 结束 | scene
#  1 | 0:24 | intro
#  2 | 0:46 | task1-tf
#  3 | 1:13 | task1-morph
#  4 | 1:49 | task2-evolution
#  5 | 2:02 | task2-void
#  6 | 2:19 | task2-cases
#  7 | 2:37 | task2-spatial
#  8 | 3:01 | task3-hist
#  9 | 4:02 | task4-brush（含操作停顿）
# 10 | 4:28 | task4-validate
# 11 | 4:58 | findings（整轨 ≤5:00）
SECTION_ENDS = [24.0, 46.0, 73.0, 109.0, 122.0, 139.0, 157.0, 181.0, 250.0, 268.0, 298.0]

MIN_CUE_SEC = 1.6
MAX_CUE_CHARS = 40

STRIP_PUNCT = set("。？！·""''「」:!?'\"[]{}")
SPACE_PUNCT = set("，、,;；…—－–—:：（）()")


def stripped_len(text: str) -> int:
    return len(strip_punctuation(text))


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
    for line in lines:
        stripped = line.strip()
        if stripped == "正文":
            in_body = True
            continue
        if not in_body:
            continue
        if stripped.startswith("----"):
            continue
        if stripped:
            paragraphs.append(stripped)
    return paragraphs


def _is_cjk(ch: str) -> bool:
    if not ch:
        return False
    o = ord(ch)
    return 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF


def _is_ascii_alnum(ch: str) -> bool:
    return ch.isascii() and ch.isalnum()


def _bad_split_at(text: str, pos: int) -> bool:
    """pos 为切分点（左段 text[:pos]，右段 text[pos:]）。"""
    if pos <= 0 or pos >= len(text):
        return False
    left, right = text[pos - 1], text[pos]
    if left.isspace() or right.isspace():
        return False
    if left.isdigit() and (right.isdigit() or right == "."):
        return True
    if left == "." and right.isdigit():
        return True
    if _is_ascii_alnum(left) and _is_ascii_alnum(right):
        return True
    if left == "%" or right == "%":
        return True
    if left == "−" or right == "−":
        return True
    return False


def _break_score(text: str, pos: int, max_chars: int) -> int:
    """越高越优先在此切分。"""
    if pos <= 0 or pos >= len(text):
        return -1
    if _bad_split_at(text, pos):
        return -1
    left, right = text[pos - 1], text[pos]
    prefix_len = stripped_len(text[:pos])
    near_limit = prefix_len >= int(max_chars * 0.82)

    if left.isspace() or right.isspace():
        return 100
    if left in SPACE_PUNCT or right in SPACE_PUNCT:
        return 90
    if _is_cjk(left) and _is_ascii_alnum(right) and near_limit:
        return 85
    if _is_ascii_alnum(left) and _is_cjk(right) and near_limit:
        return 85
    if _is_cjk(left) and _is_cjk(right) and near_limit:
        return 55
    if not _is_ascii_alnum(left) and _is_cjk(right) and near_limit:
        return 45
    if _is_cjk(left) and not _is_ascii_alnum(right) and near_limit:
        return 45
    return -1


def _find_cut_pos(text: str, max_chars: int) -> int:
    """在 text 上找首个 chunk 的安全切分位置（不含），尽量填满 max_chars。"""
    if stripped_len(text) <= max_chars:
        return len(text)
    best = 1
    best_score = -1
    for i in range(1, len(text) + 1):
        if stripped_len(text[:i]) > max_chars:
            break
        score = _break_score(text, i, max_chars)
        if score < 0:
            continue
        if score > best_score or (score == best_score and i > best):
            best_score = score
            best = i
    if best_score >= 0:
        return best
    cut = 1
    while cut < len(text) and stripped_len(text[: cut + 1]) <= max_chars:
        if not _bad_split_at(text, cut + 1):
            best = cut + 1
        cut += 1
    return max(1, min(best, len(text)))


def force_split(seg: str, max_chars: int) -> list[str]:
    """超长句按安全断点切分，避免拆开小数/英文/百分比。"""
    seg = seg.strip()
    if stripped_len(seg) <= max_chars:
        return [seg]
    parts: list[str] = []
    rest = seg
    while rest:
        if stripped_len(rest) <= max_chars:
            parts.append(rest)
            break
        cut = _find_cut_pos(rest, max_chars)
        parts.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    return parts


_ORPHAN_RE = re.compile(r"^(oid|\d+%|\d{1,4})$")
_SHORT_EN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9./]*$")


def _join_chunks(left: str, right: str) -> str:
    if not left:
        return right
    if not right:
        return left
    if (left[-1].isascii() and _is_cjk(right[0])) or (_is_cjk(left[-1]) and right[0].isascii()):
        return f"{left} {right}"
    return left + right


_PREFIX_ORPHAN_RE = re.compile(r"^(的|与 |及|到 |对应)")
_NUMERIC_ONLY_RE = re.compile(r"^[\d.]+%?$")


def _is_prefix_orphan(chunk: str) -> bool:
    cur = chunk.strip()
    if _PREFIX_ORPHAN_RE.match(cur):
        return stripped_len(cur) <= 14
    sp = strip_punctuation(cur)
    if _NUMERIC_ONLY_RE.match(sp):
        return True
    return sp in {"Top", "p99"} or sp.startswith("Bottom")


def merge_orphan_fragments(chunks: list[str], max_chars: int = MAX_CUE_CHARS) -> list[str]:
    """合并 force_split 产生的英文/数字残片（后缀并上条，前缀并下条）。"""
    if not chunks:
        return chunks

    # 前缀残片（如 cosmic）并到下一条
    forward: list[str] = []
    idx = 0
    while idx < len(chunks):
        cur = chunks[idx]
        cur_stripped = strip_punctuation(cur)
        if (
            idx + 1 < len(chunks)
            and bool(_SHORT_EN_RE.match(cur_stripped))
            and len(cur_stripped) <= 8
            and stripped_len(cur + chunks[idx + 1]) <= max_chars
        ):
            forward.append(_join_chunks(cur, chunks[idx + 1]))
            idx += 2
            continue
        forward.append(cur)
        idx += 1

    # 后缀 / 前缀残片并到相邻条目
    merged: list[str] = [forward[0]]
    for chunk in forward[1:]:
        prev = merged[-1]
        cur_stripped = strip_punctuation(chunk)
        prev_stripped = strip_punctuation(prev)
        is_suffix = bool(_ORPHAN_RE.match(cur_stripped)) or (
            len(cur_stripped) <= 2 and prev_stripped and prev_stripped[-1].isascii()
        )
        if is_suffix and stripped_len(prev + chunk) <= max_chars:
            merged[-1] = _join_chunks(prev, chunk)
        elif _is_prefix_orphan(chunk) and stripped_len(prev + chunk) <= max_chars:
            merged[-1] = _join_chunks(prev, chunk)
        else:
            merged.append(chunk)

    # 单字英文前缀（如 Top）并到下一条
    forward2: list[str] = []
    idx = 0
    while idx < len(merged):
        cur = merged[idx]
        sp = strip_punctuation(cur)
        if (
            idx + 1 < len(merged)
            and sp in {"Top"}
            and stripped_len(cur + merged[idx + 1]) <= max_chars + 4
        ):
            forward2.append(_join_chunks(cur, merged[idx + 1]))
            idx += 2
            continue
        forward2.append(cur)
        idx += 1
    return forward2


def split_for_subtitles(text: str, max_chars: int = MAX_CUE_CHARS) -> list[str]:
    """先按句号/分号切句，过长再按逗号切，仍过长则按安全断点切。"""
    segments: list[str] = []
    for seg in re.split(r"[。；]", text):
        seg = seg.strip()
        if seg:
            segments.append(seg)

    result: list[str] = []
    for seg in segments:
        if stripped_len(seg) <= max_chars:
            result.append(seg)
            continue
        clauses = [c.strip() for c in seg.split("，") if c.strip()]
        buf = ""
        for cl in clauses:
            trial = f"{buf}，{cl}" if buf else cl
            if stripped_len(trial) <= max_chars or not buf:
                buf = trial
            else:
                result.extend(force_split(buf, max_chars))
                buf = cl
        if buf:
            if stripped_len(buf) <= max_chars:
                result.append(buf)
            else:
                result.extend(force_split(buf, max_chars))

    final: list[str] = []
    for seg in result:
        final.extend(force_split(seg, max_chars))
    polished: list[str] = []
    for seg in final:
        if stripped_len(seg) <= max_chars:
            polished.append(seg)
        else:
            polished.extend(force_split(seg, max_chars))
    return merge_orphan_fragments(polished, max_chars)


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
    weights = [max(stripped_len(s), 1) for s in sentences]
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
            f"TTS 正文应为 {len(SECTION_ENDS)} 行，实际 {len(paragraphs)} 行。"
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


def _normalize_for_compare(text: str) -> str:
    return strip_punctuation(text).replace(" ", "")


def validate_cues(paragraphs: list[str], cues: list[tuple[float, float, str]]) -> list[str]:
    errors: list[str] = []
    tts_norm = _normalize_for_compare("".join(paragraphs))
    srt_norm = _normalize_for_compare("".join(c[2] for c in cues))
    if tts_norm != srt_norm:
        errors.append(f"字幕文本与 TTS 不一致（{len(tts_norm)} vs {len(srt_norm)} 字）")

    for i, (start, end, text) in enumerate(cues):
        if end <= start:
            errors.append(f"条目 #{i + 1} 时长无效: {start} -> {end}")
        slen = stripped_len(text)
        if slen > MAX_CUE_CHARS:
            errors.append(f"条目 #{i + 1} 超长 ({slen} 字): {strip_punctuation(text)[:40]}…")
        if i > 0:
            prev_end = cues[i - 1][1]
            if start < prev_end - 0.001:
                errors.append(f"条目 #{i + 1} 与 #{i} 时间重叠")
            if abs(start - prev_end) > 0.01:
                errors.append(f"条目 #{i + 1} 与 #{i} 时间未衔接 ({prev_end:.3f} -> {start:.3f})")

    if cues and abs(cues[-1][1] - SECTION_ENDS[-1]) > 0.01:
        errors.append(f"总时长 {cues[-1][1]:.1f}s 与目标 {SECTION_ENDS[-1]}s 不符")

    for i, (start, end, text) in enumerate(cues, 1):
        sp = strip_punctuation(text)
        if _ORPHAN_RE.match(sp) or sp in {"012", "势"}:
            errors.append(f"条目 #{i} 疑似残片切分: {sp!r}")

    return errors


def main() -> None:
    paragraphs = load_tts_paragraphs(TTS)
    cues = build_cues(paragraphs)
    errors = validate_cues(paragraphs, cues)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)

    OUT.write_text(build_srt(cues), encoding="utf-8-sig")
    stripped = [strip_punctuation(c[2]) for c in cues]
    max_len = max(len(s) for s in stripped)
    print(f"Source: {TTS.name} ({len(paragraphs)} paragraphs)")
    print(f"Wrote {OUT} ({len(cues)} cues, ~{cues[-1][1]:.0f}s, max {max_len} chars/cue)")
    print("Validation: OK (monotonic, text match, no orphan splits)")


if __name__ == "__main__":
    main()
