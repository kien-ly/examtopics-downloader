import re
import os
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent


def extract_answers(answer_text: str, options_dict: dict) -> list:
    """
    Extract correct answers from answer text and map to options.
    
    Args:
        answer_text: The answer text (e.g., "A", "AD", "CE")
        options_dict: Dictionary mapping letters to option text
    
    Returns:
        List of correct answer texts
    """
    # Remove any whitespace and split by characters
    answer_letters = list(answer_text.strip())
    
    correct_answers = []
    for letter in answer_letters:
        if letter in options_dict:
            correct_answers.append(options_dict[letter])
    
    return correct_answers


def parse_question_with_answer(question_text: str) -> dict:
    """
    Parse a question block to extract question, options, and answer.
    
    Args:
        question_text: Raw question text
    
    Returns:
        Dictionary with question, options, and correct answers
    """
    result = {
        'title': '',
        'question': '',
        'correct_answers': []
    }
    
    # Extract title (e.g. ## question 1)
    title_match = re.search(r'(?mi)^##\s*question(?:\s+(\d+))?', question_text)
    if title_match:
        num = title_match.group(1)
        result['title'] = f"question {int(num)}" if num else 'question'

    # Remove any Suggested Answer lines that may appear
    qt = re.sub(r'(?mi)^\s*Suggested Answer:.*$', '', question_text, flags=re.MULTILINE)

    # Extract question content (text between header and first option or Answer)
    # We consider options that start with a capital letter followed by a dot, e.g. "A. "
    q_match = re.search(r'(?ms)^##\s*question.*?\n\n(.*?)(?=\n\n[A-Z]\.\s|\n\n\*\*Answer:|$)', qt)
    if q_match:
        result['question'] = q_match.group(1).strip()

    # Extract options like 'A. Option text' (multi-line allowed until next option or Answer)
    options_dict = {}
    option_pattern = r'(?ms)\n\n([A-Z])\.\s+(.*?)(?=\n\n[A-Z]\.\s|\n\n\*\*Answer:|$)'
    options = re.findall(option_pattern, qt)
    for letter, text in options:
        options_dict[letter] = text.strip()

    # Extract answer (letters inside bold Answer marker)
    answer_match = re.search(r'\*\*Answer:\s*([A-Z]+)\*\*', qt)
    if answer_match:
        answer_text = answer_match.group(1)
        result['correct_answers'] = extract_answers(answer_text, options_dict)
    
    return result


def process_exam_with_answers(input_file: str, output_dir: str) -> None:
    """
    Process exam file to extract questions and correct answers only.
    
    Args:
        input_file: Path to input markdown file (relative to project root)
        output_dir: Directory to save output file (relative to project root)
    """
    # Get project root and resolve paths
    project_root = get_project_root()
    input_path = project_root / input_file
    output_path = project_root / output_dir
    
    # Read input file
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract exam name from file path
    exam_name = input_path.stem
    
    # Split content into question sections using '## question' headers
    header_re = re.compile(r'(?mi)^##\s*question(?:\s+\d+)?')
    matches = list(header_re.finditer(content))

    processed_questions = []
    if not matches:
        # fallback: parse whole file as single question block
        parsed = parse_question_with_answer(content)
        if parsed['question'] and parsed['correct_answers']:
            output = f"## {parsed['title']}\n\n"
            output += f"{parsed['question']}\n\n"
            output += "**Correct Answer(s):**\n\n"
            for answer in parsed['correct_answers']:
                output += f"- {answer}\n"
            processed_questions.append(output)
    else:
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            section = content[start:end]
            parsed = parse_question_with_answer(section)
            if parsed['question'] and parsed['correct_answers']:
                output = f"## {parsed['title']}\n\n"
                output += f"{parsed['question']}\n\n"
                output += "**Correct Answer(s):**\n\n"
                for answer in parsed['correct_answers']:
                    output += f"- {answer}\n"
                processed_questions.append(output)
    
    # Create output content
    output_content = f"# Exam Questions & Answers - {exam_name.upper()}\n\n"
    output_content += "\n\n----------------------------------------\n\n".join(processed_questions)
    
    # Create output directory if not exists
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Write output file
    output_file = output_path / f"{exam_name}-answers.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_content)
    
    print(f"✓ Processed: {input_path}")
    print(f"✓ Output saved to: {output_file}")
    print(f"✓ Total questions: {len(processed_questions)}")


def process_all_exams_with_answers(input_dir: str = "data/raw/aws", 
                                   output_dir: str = "data/answers/aws") -> None:
    """
    Process all exam files to extract questions and answers.
    
    Args:
        input_dir: Directory containing raw exam files (relative to project root)
        output_dir: Directory to save processed files (relative to project root)
    """
    # Get project root and resolve paths
    project_root = get_project_root()
    input_path = project_root / input_dir
    
    # Find all markdown files
    exam_files = list(input_path.glob("*.md"))
    
    if not exam_files:
        print(f"No markdown files found in {input_path}")
        return
    
    print(f"Found {len(exam_files)} exam file(s) to process\n")
    
    # Process each file
    for exam_file in exam_files:
        try:
            # Convert to relative path from project root
            relative_path = exam_file.relative_to(project_root)
            process_exam_with_answers(str(relative_path), output_dir)
            print()
        except Exception as e:
            print(f"✗ Error processing {exam_file}: {str(e)}\n")


if __name__ == "__main__":
    # Process all exam files
    # process_all_exams_with_answers()
    
    # Process single file
    process_exam_with_answers(
        # "data/raw/aws/mla-c01.md",
        "data/silver/aws/dop-c02.md",
        "data/answers/aws"
    )