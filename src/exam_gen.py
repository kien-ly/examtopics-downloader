import re
import os
from pathlib import Path


def process_exam_file(input_file: str, output_dir: str) -> None:
    """
    Process exam file to extract questions and options only.
    
    Args:
        input_file: Path to input markdown file
        output_dir: Directory to save output file
    """
    # Read input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract exam name from file path
    input_path = Path(input_file)
    exam_name = input_path.stem
    
    # Split content into question sections using headings like "## question <n>"
    header_re = re.compile(r'(?mi)^##\s*question(?:\s+(\d+))?')
    matches = list(header_re.finditer(content))

    processed_questions = []
    if not matches:
        # fallback: treat whole file as one block
        body = content
        # remove suggested/answer/timestamp/view footers if present
        body = re.split(r'\n\*\*Answer:', body, maxsplit=1)[0]
        body = re.sub(r'(?mi)^\s*Suggested Answer:.*$', '', body, flags=re.MULTILINE)
        body = body.strip()
        if body:
            processed_questions.append(body)
    else:
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            qnum = m.group(1) or ''
            section = content[start:end].strip()

            # remove the header line and rebuild a normalized header
            # split section into lines, drop the first header line
            lines = section.splitlines()
            body_lines = lines[1:] if len(lines) > 1 else []
            body = '\n'.join(body_lines).rstrip()

            # remove Suggested Answer lines that appear before choices
            body = re.sub(r'(?mi)^\s*Suggested Answer:.*$', '', body, flags=re.MULTILINE)

            # truncate at the bold Answer marker if present (we want only question + choices)
            body = re.split(r'\n\*\*Answer:', body, maxsplit=1)[0]

            # remove Timestamp and View on ExamTopics links if they somehow remain
            body = re.sub(r'(?mi)^\*\*Timestamp:.*$', '', body, flags=re.MULTILINE)
            body = re.sub(r'(?mi)^\[View on ExamTopics\].*$', '', body, flags=re.MULTILINE)

            # collapse trailing blank lines
            body = body.strip()

            header = '## question' + (f' {int(qnum)}' if qnum else '')
            block = header
            if body:
                block += '\n\n' + body
            processed_questions.append(block)
    
    # Create output content
    output_content = f"# Exam Topics Questions - {exam_name.upper()}\n\n"
    output_content += "\n\n----------------------------------------\n\n".join(processed_questions)
    
    # Create output directory if not exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Write output file
    output_file = os.path.join(output_dir, f"{exam_name}-exam.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_content)
    
    print(f"✓ Processed: {input_file}")
    print(f"✓ Output saved to: {output_file}")


def process_all_exams(input_dir: str = "data/raw/aws", 
                      output_dir: str = "data/exam/aws") -> None:
    """
    Process all exam files in the input directory.
    
    Args:
        input_dir: Directory containing raw exam files
        output_dir: Directory to save processed exam files
    """
    input_path = Path(input_dir)
    
    # Find all markdown files
    exam_files = list(input_path.glob("*.md"))
    
    if not exam_files:
        print(f"No markdown files found in {input_dir}")
        return
    
    print(f"Found {len(exam_files)} exam file(s) to process\n")
    
    # Process each file
    for exam_file in exam_files:
        try:
            process_exam_file(str(exam_file), output_dir)
            print()
        except Exception as e:
            print(f"✗ Error processing {exam_file}: {str(e)}\n")


if __name__ == "__main__":
    # Process all exam files
    # process_all_exams()
    process_exam_file(
    # "data/raw/aws/mla-c01.md",
    "data/silver/aws/dop-c02.md",
    "data/exam/aws"
)