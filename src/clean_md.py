# -*- coding: utf-8 -*-
"""
Simple cleaner for ExamTopics .md files:
- Keeps "## question <N>" as section headers
- Removes duplicate "Question #: <N>" (and optionally "Topic #: <N>")
- Sorts question sections by numeric question id
- Collapses repeated blank lines

Usage:
    python src/clean_md.py data/raw/aws/sap-c02.md -o data/silver/aws/sap-c02.md
    python src/clean_md.py data/raw/aws/dop-c02.md -o data/silver/aws/dop-c02.md
"""
import re
import argparse
from pathlib import Path

# Match headers that contain the word "question <N>" anywhere on the header line.
# This allows lines like "## Exam ... question 358 discussion" to be detected.
HEADER_RE = re.compile(r'(?mi)^##.*?question\s+(\d+)\b')
REMOVE_LINE_RE = re.compile(
    r'^\s*(Question\s*#\s*:?\s*\d+|Question\s*:?\s*\d+|Question\s*Number\s*:?\s*\d+)\s*$',
    re.IGNORECASE
)
TOPIC_LINE_RE = re.compile(r'^\s*Topic\s*#\s*:?\s*\d+\s*$', re.IGNORECASE)


def normalize_header(num: str) -> str:
    return f'## question {int(num)}'


def clean_section_text(text: str, remove_topic: bool) -> str:
    lines = text.splitlines()
    out = []
    prev_blank = False
    for ln in lines:
        # skip duplicate Question #: 169 lines
        if REMOVE_LINE_RE.match(ln):
            continue
        if remove_topic and TOPIC_LINE_RE.match(ln):
            continue
        # collapse multiple blank lines to a single blank
        if not ln.strip():
            if not prev_blank:
                out.append('')
            prev_blank = True
        else:
            out.append(ln.rstrip())
            prev_blank = False
    # If a Timestamp line appears, remove it and everything after it
    # e.g. lines like: **Timestamp: April 23, 2025, 4:15 a.m.**
    ts_re = re.compile(r'(?i)^\s*\*\*Timestamp:')
    # Also consider the following ExamTopics view link that often follows
    view_re = re.compile(r'(?i)^\s*\[View on ExamTopics\]')

    # find first occurrence of timestamp or view link and truncate from there
    cut_index = None
    for idx, ln in enumerate(out):
        if ts_re.match(ln) or view_re.match(ln):
            cut_index = idx
            break
    if cut_index is not None:
        out = out[:cut_index]

    # strip leading/trailing blanks
    while out and out[0] == '':
        out.pop(0)
    while out and out[-1] == '':
        out.pop()
    return '\n'.join(out)


def split_into_sections(text: str):
    matches = list(HEADER_RE.finditer(text))
    if not matches:
        return [("__preamble__", text)]
    sections = []
    # preamble
    first = matches[0]
    preamble = text[: first.start()].rstrip()
    if preamble:
        sections.append(("__preamble__", preamble))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        qnum = int(m.group(1))
        # extract section raw (including header)
        section_raw = text[start:end].splitlines()
        # header line may include extra; normalize it
        # drop original header line and rebuild canonical header
    # reconstruct body (lines after header)
        body_lines = section_raw[1:] if len(section_raw) > 1 else []
        body = '\n'.join(body_lines).rstrip()
        sections.append((qnum, body))
    return sections


def main():
    p = argparse.ArgumentParser(description="Clean and sort ExamTopics markdown question file.")
    p.add_argument("input", type=Path, help="input .md file")
    p.add_argument("-o", "--output", type=Path, default=None, help="output .md file")
    p.add_argument("--remove-topic", action="store_true", help="also remove 'Topic #: <n>' lines")
    args = p.parse_args()

    text = args.input.read_text(encoding="utf-8")
    sections = split_into_sections(text)

    # if split returned only preamble in a single tuple, write it back
    if len(sections) == 1 and sections[0][0] == "__preamble__":
        out_text = sections[0][1].strip() + "\n"
        out_path = args.output or (args.input.parent / (args.input.stem + ".cleaned.md"))
        out_path.write_text(out_text, encoding="utf-8")
        print(f"Written {out_path}")
        return

    preamble = ""
    if sections and sections[0][0] == "__preamble__":
        preamble = sections[0][1].rstrip()
        sections = sections[1:]

    # sections is list of (qnum, body)
    cleaned = []
    for qnum, body in sections:
        body_clean = clean_section_text(body, remove_topic=args.remove_topic)
        block = normalize_header(qnum)
        if body_clean:
            block += '\n\n' + body_clean
        cleaned.append((qnum, block))

    # sort by question number
    cleaned.sort(key=lambda x: x[0])

    parts = []
    if preamble:
        parts.append(preamble.rstrip())
        parts.append('')
    for _, blk in cleaned:
        parts.append(blk.rstrip())
        parts.append('')  # blank line between sections

    out_text = '\n'.join(parts).rstrip() + '\n'

    out_path = args.output or (args.input.parent / (args.input.stem + "-cleaned.md"))
    out_path.write_text(out_text, encoding="utf-8")
    print(f"Cleaned file written to: {out_path}")


if __name__ == "__main__":
    main()