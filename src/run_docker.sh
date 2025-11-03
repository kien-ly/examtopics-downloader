#!/bin/bash

# This script can be run from anywhere.
# It assumes you have built the Docker image with the tag 'examtopics-downloader' from the project root.
# Example build command: docker build -t examtopics-downloader .

# Get the absolute path to the project root directory by going up one level from the script's directory
PROJECT_ROOT=$(cd "$(dirname "$0")/.."; pwd)
platform="microsoft"

# Ensure the results directories exist
mkdir -p "$PROJECT_ROOT/results/raw"
mkdir -p "$PROJECT_ROOT/results/saved-links"

# Check if the CSV file exists
CSV_FILE="$PROJECT_ROOT/src/${platform}_cert.csv"
if [ ! -f "$CSV_FILE" ]; then
    echo "Error: CSV file not found at $CSV_FILE"
    exit 1
fi

# Loop through aws_cert.csv, skip header, run docker command for each certification
tail -n +2 "$CSV_FILE" | while IFS=, read -r platform title code slug link
do
    # Skip empty lines
    [ -z "$slug" ] && continue

    echo "Processing $code ($slug) using Docker..."

    # The output paths (-o, -save-links) are absolute paths inside the container.
    # We mount the local project's 'results' directory to '/app/results' in the container.
    docker run --rm \
        -v "$PROJECT_ROOT/results:/app/results" \
        examtopics-downloader \
        -p "$platform" \
        -t "$title" \
        -s "$slug" \
        -o "/app/results/raw/$code.md" \
        -save-links "/app/results/saved-links/$code-link.txt" \
        -no-cache

    echo "Finished processing $code. Waiting 3 seconds..."
    sleep 3
done

echo "All certifications processed."
