import sys
import subprocess
from pathlib import Path

def ensure_markdown():
    try:
        import markdown
        return markdown
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown"])
        import markdown
        return markdown

def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent

def convert_md_to_html(input_md: str):
    project_root = get_project_root()
    input_path = (project_root / input_md).resolve()
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return 1

    md = ensure_markdown()
    text = input_path.read_text(encoding="utf-8")
    html_body = md.markdown(text, extensions=["fenced_code", "tables", "toc", "nl2br", "attr_list"])

    title = input_path.stem
    html = f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-light.min.css">
  <style>body{{padding:24px}} .markdown-body{{box-sizing:border-box;max-width:980px;margin:0 auto}}</style>
</head>
<body>
  <article class="markdown-body">
  {html_body}
  </article>
</body>
</html>"""

    output_path = input_path.with_suffix(".html")
    output_path.write_text(html, encoding="utf-8")
    print(f"✓ HTML saved to: {output_path}")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(convert_md_to_html(sys.argv[1]))
    # default: convert the SAP file in your repo
    sys.exit(convert_md_to_html("data/answers/aws/sap-c02-answers.md"))