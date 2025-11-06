import re
import os
import shutil

def remove_timestamp_and_links(input_file, output_file):
    # Read entire file and remove any block that matches the provided regex
    # User requested regex: \*\*Timestamp:[\s\S]*?/\)
    pattern = re.compile(r"\*\*Timestamp:[\s\S]*?/\)")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Lỗi khi đọc file {input_file}: {e}")
        return 0

    matches = pattern.findall(content)
    removed_count = len(matches)
    if removed_count > 0:
        new_content = pattern.sub('', content)
    else:
        new_content = content

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Đã ghi {len(new_content.splitlines())} dòng vào {output_file}.")
    except Exception as e:
        print(f"Lỗi khi ghi file: {e}")
        return 0

    print(f"Đã xóa {removed_count} match(ở) theo regex.")
    return removed_count

# Sử dụng
input_file = '/Users/kien.ly/Library/CloudStorage/OneDrive-BangkokSolution/my-project/examtopics-downloader/results/raw/del_url/clf-c02.md'
output_file = '/Users/kien.ly/Library/CloudStorage/OneDrive-BangkokSolution/my-project/examtopics-downloader/results/raw/del_url/clf-c02-cleaned.md'

print(f"Input file: {input_file}")
print(f"Output file: {output_file}")

removed = remove_timestamp_and_links(input_file, output_file)

# Rename để thay thế file gốc
try:
    shutil.move(output_file, input_file)
    print("File đã được cập nhật.")
except Exception as e:
    print(f"Lỗi khi cập nhật file: {e}")