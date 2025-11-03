#!/bin/bash

    docker run --rm \
        -v "$(pwd)/results:/app/output" \
        -v "$(pwd)/env:/app/env" \
        -v "$(pwd)/examtopics-data:/app/examtopics-data" \
        examtopics-downloader \
        -p microsoft -s "$slug" -o "/app/output/raw/azure/$code.md" -save-links -output-save-links "/app/output/saved-links/$code-link.txt"nge to project root directory
cd ..

# Build Docker image
echo "Building Docker image..."
docker build -t examtopics-downloader .

# Loop through scraped slugs, run Docker container for each certification
echo "Getting certification slugs..."
slugs=$(docker run --rm \
    -v "$(pwd)/results:/app/output" \
    -v "$(pwd)/env:/app/env" \
    -v "$(pwd)/examtopics-data:/app/examtopics-data" \
    examtopics-downloader \
    -p microsoft -list-slugs)

for slug in $slugs
do
    echo "Processing $slug..."
    docker run --rm \
        -v "$(pwd)/results:/app/output" \
        -v "$(pwd)/env:/app/env" \
        -v "$(pwd)/examtopics-data:/app/examtopics-data" \
        examtopics-downloader \
        -p microsoft -s "$slug" -no-cache -o "/app/output/raw/azure/$slug.md" -save-links -output-save-links "/app/output/saved-links/$slug-link.txt"
    sleep 3
done

echo "All certifications processed."