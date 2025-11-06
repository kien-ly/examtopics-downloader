#!/bin/bash

# Build Docker image
echo "Building Docker image..."
docker build -t examtopics-batch .

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "✅ Build successful!"
echo ""
echo "Running batch processing..."
echo ""

# Run Docker container with volume mounts
docker run --rm \
  -v "$(pwd)/src:/app/src" \
  -v "$(pwd)/results:/app/results" \
  examtopics-batch \
  -csv /app/src/microsoft_cert.csv \
  -p microsoft \
  -output-dir /app/results/raw \
  -links-dir /app/results/saved-links \
  -sleep 3 \
  -no-cache

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Processing complete!"
else
    echo ""
    echo "❌ Processing failed!"
    exit 1
fi
