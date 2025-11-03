#!/usr/bin/env python3

import csv
import os

def create_microsoft_cert_csv():
    # Read microsoft-link.txt
    with open('/Users/kien.ly/Library/CloudStorage/OneDrive-BangkokSolution/my-project/examtopics-downloader/env/microsoft-link.txt', 'r') as f:
        links = [line.strip() for line in f if line.strip()]

    # Create CSV
    csv_path = '/Users/kien.ly/Library/CloudStorage/OneDrive-BangkokSolution/my-project/examtopics-downloader/src/microsoft_cert.csv'

    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(['Platform', 'Certification Title', 'Certification Code', 'Certification Slug', 'Certification link'])

        for link in links:
            # Parse slug from URL
            # URL format: https://www.examtopics.com/exams/microsoft/{slug}/
            slug = link.split('/')[-2]  # Get slug from URL

            # For Microsoft, code is usually the same as slug
            code = slug

            # Create a basic title (we can improve this later)
            title = f"Microsoft {slug}"

            writer.writerow(['Microsoft', title, code, slug, link])

    print(f"Created {csv_path} with {len(links)} certifications")

if __name__ == "__main__":
    create_microsoft_cert_csv()