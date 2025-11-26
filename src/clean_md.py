# -*- coding: utf-8 -*-
"""
ExamTopics Markdown Cleaner

A robust cleaner for ExamTopics .md files that:
- Normalizes section headers to "## question <N>" format
- Removes duplicate "Question #: <N>" and optionally "Topic #: <N>" lines
- Sorts question sections by numeric question ID
- Collapses repeated blank lines
- Removes timestamps and ExamTopics view links

Usage:
    Single file:
        python src/clean_md.py data/raw/aws/sap-c02.md -o data/silver/aws/sap-c02.md
    
    Batch process folder:
        python src/clean_md.py data/raw/aws/ -o data/silver/aws/
        python src/clean_md.py data/raw/azure/ -o data/silver/azure/ --remove-topic
"""
import argparse
import logging
import re
import sys
from pathlib import Path
from typing import List, Tuple, Union

# Match headers that contain the word "question" followed by a question number anywhere on the header line.
# Accept formats like "question 1", "question #1", or "question: 1" embedded in long headers.
HEADER_RE = re.compile(r'(?mi)^##.*?question[^\d]*(\d+)\b')

# Pattern to match redundant question number lines
REMOVE_LINE_RE = re.compile(
    r'^\s*(Question\s*#\s*:?\s*\d+|Question\s*:?\s*\d+|Question\s*Number\s*:?\s*\d+)\s*$',
    re.IGNORECASE
)

# Pattern to match topic lines
TOPIC_LINE_RE = re.compile(r'^\s*Topic\s*#\s*:?\s*\d+\s*$', re.IGNORECASE)

# Pattern to match timestamp lines
TIMESTAMP_RE = re.compile(r'(?i)^\s*\*\*Timestamp:')

# Pattern to match ExamTopics view links
VIEW_LINK_RE = re.compile(r'(?i)^\s*\[View on ExamTopics\]')

# Type alias for sections
Section = Tuple[Union[str, int], str]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_header(num: Union[str, int]) -> str:
    """
    Normalize question header to canonical format.
    
    Args:
        num: Question number as string or integer
        
    Returns:
        Normalized header string in format "## question <N>"
        
    Examples:
        >>> normalize_header("42")
        '## question 42'
        >>> normalize_header(42)
        '## question 42'
    """
    return f'## question {int(num)}'


def clean_section_text(text: str, remove_topic: bool) -> str:
    """
    Clean and normalize section text by removing redundant lines and collapsing blanks.
    
    Args:
        text: Raw section text to clean
        remove_topic: If True, also remove "Topic #: <n>" lines
        
    Returns:
        Cleaned text with normalized whitespace and removed metadata
        
    Notes:
        - Removes duplicate "Question #: <N>" lines
        - Optionally removes "Topic #: <N>" lines
        - Collapses multiple blank lines to single blank
        - Removes timestamp and ExamTopics view links
        - Strips leading and trailing blank lines
    """
    lines = text.splitlines()
    out = []
    prev_blank = False
    
    for ln in lines:
        # Skip duplicate Question #: 169 lines
        if REMOVE_LINE_RE.match(ln):
            continue
        if remove_topic and TOPIC_LINE_RE.match(ln):
            continue
            
        # Collapse multiple blank lines to a single blank
        if not ln.strip():
            if not prev_blank:
                out.append('')
            prev_blank = True
        else:
            out.append(ln.rstrip())
            prev_blank = False
    
    # Find first occurrence of timestamp or view link and truncate from there
    cut_index = None
    for idx, ln in enumerate(out):
        if TIMESTAMP_RE.match(ln) or VIEW_LINK_RE.match(ln):
            cut_index = idx
            break
    
    if cut_index is not None:
        out = out[:cut_index]
    
    # Strip leading/trailing blanks
    while out and out[0] == '':
        out.pop(0)
    while out and out[-1] == '':
        out.pop()
        
    return '\n'.join(out)


def split_into_sections(text: str) -> List[Section]:
    """
    Split markdown text into sections based on question headers.
    
    Args:
        text: Complete markdown file content
        
    Returns:
        List of tuples (question_num, body_text) or [("__preamble__", text)] if no sections found
        
    Notes:
        - Recognizes headers matching pattern: ## question <N>
        - First section may be preamble (non-question content)
        - Each section includes normalized header and body
    """
    matches = list(HEADER_RE.finditer(text))
    if not matches:
        return [("__preamble__", text)]
        
    sections = []
    
    # Extract preamble if exists
    first = matches[0]
    preamble = text[:first.start()].rstrip()
    if preamble:
        sections.append(("__preamble__", preamble))
    
    # Extract each question section
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        qnum = int(m.group(1))
        
        # Extract section raw (including header)
        section_raw = text[start:end].splitlines()
        
        # Reconstruct body (lines after header)
        body_lines = section_raw[1:] if len(section_raw) > 1 else []
        body = '\n'.join(body_lines).rstrip()
        sections.append((qnum, body))
        
    return sections


def process_single_file(input_path: Path, output_path: Path, remove_topic: bool) -> bool:
    """
    Process a single markdown file: clean, normalize, and sort questions.
    
    Args:
        input_path: Path to input .md file
        output_path: Path to output .md file
        remove_topic: If True, remove "Topic #: <n>" lines
        
    Returns:
        True if processing succeeded, False otherwise
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        PermissionError: If unable to write output file
    """
    try:
        logger.info(f"Processing: {input_path}")
        
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return False
            
        text = input_path.read_text(encoding="utf-8")
        sections = split_into_sections(text)

        # If split returned only preamble in a single tuple, write it back
        if len(sections) == 1 and sections[0][0] == "__preamble__":
            out_text = sections[0][1].strip() + "\n"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(out_text, encoding="utf-8")
            logger.info(f"Written (preamble only): {output_path}")
            return True

        preamble = ""
        if sections and sections[0][0] == "__preamble__":
            preamble = sections[0][1].rstrip()
            sections = sections[1:]

        # Sections is list of (qnum, body)
        cleaned = []
        for qnum, body in sections:
            body_clean = clean_section_text(body, remove_topic=remove_topic)
            block = normalize_header(qnum)
            if body_clean:
                block += '\n\n' + body_clean
            cleaned.append((qnum, block))

        # Sort by question number
        cleaned.sort(key=lambda x: x[0])

        parts = []
        if preamble:
            parts.append(preamble.rstrip())
            parts.append('')
        for _, blk in cleaned:
            parts.append(blk.rstrip())
            parts.append('')  # Blank line between sections

        out_text = '\n'.join(parts).rstrip() + '\n'

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(out_text, encoding="utf-8")
        logger.info(f"✓ Cleaned file written to: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing {input_path}: {e}")
        return False


def process_folder(input_folder: Path, output_folder: Path, remove_topic: bool) -> Tuple[int, int]:
    """
    Batch process all .md files in a folder.
    
    Args:
        input_folder: Path to folder containing input .md files
        output_folder: Path to folder for output files
        remove_topic: If True, remove "Topic #: <n>" lines
        
    Returns:
        Tuple of (success_count, total_count)
        
    Notes:
        - Recursively processes all .md files in input folder
        - Preserves subdirectory structure in output folder
        - Skips non-.md files
    """
    if not input_folder.exists():
        logger.error(f"Input folder not found: {input_folder}")
        return 0, 0
        
    if not input_folder.is_dir():
        logger.error(f"Input path is not a folder: {input_folder}")
        return 0, 0
    
    # Find all .md files recursively
    md_files = list(input_folder.rglob("*.md"))
    
    if not md_files:
        logger.warning(f"No .md files found in: {input_folder}")
        return 0, 0
    
    logger.info(f"Found {len(md_files)} markdown file(s) to process")
    
    success_count = 0
    for input_path in md_files:
        # Calculate relative path to preserve directory structure
        relative_path = input_path.relative_to(input_folder)
        output_path = output_folder / relative_path
        
        if process_single_file(input_path, output_path, remove_topic):
            success_count += 1
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing complete: {success_count}/{len(md_files)} files succeeded")
    logger.info(f"{'='*60}")
    
    return success_count, len(md_files)


def main():
    """
    Main entry point for the ExamTopics markdown cleaner.
    
    Parses command-line arguments and processes either a single file or
    an entire folder of markdown files.
    """
    p = argparse.ArgumentParser(
        description="Clean and sort ExamTopics markdown question files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Single file:
    %(prog)s data/raw/aws/sap-c02.md -o data/silver/aws/sap-c02.md
    
  Batch process folder:
    %(prog)s data/raw/aws/ -o data/silver/aws/
    %(prog)s data/raw/azure/ -o data/silver/azure/ --remove-topic
        """
    )
    p.add_argument("input", type=Path, help="input .md file or folder")
    p.add_argument("-o", "--output", type=Path, required=True, 
                   help="output .md file or folder")
    p.add_argument("--remove-topic", action="store_true", 
                   help="also remove 'Topic #: <n>' lines")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="enable verbose logging")
    args = p.parse_args()
    
    # Configure logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    input_path = args.input
    output_path = args.output
    
    # Determine if processing single file or folder
    if input_path.is_file():
        # Single file processing
        if output_path.is_dir():
            # If output is a directory, use same filename
            output_path = output_path / input_path.name
        
        success = process_single_file(input_path, output_path, args.remove_topic)
        sys.exit(0 if success else 1)
        
    elif input_path.is_dir():
        # Folder processing
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
        elif not output_path.is_dir():
            logger.error(f"Output path exists but is not a directory: {output_path}")
            sys.exit(1)
        
        success_count, total_count = process_folder(input_path, output_path, args.remove_topic)
        sys.exit(0 if success_count == total_count else 1)
        
    else:
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()