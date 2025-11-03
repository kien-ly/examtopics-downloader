#!/bin/bash

# Loop through aws_cert.csv, skip header, run go command for each certification
tail -n +2 ../env/aws_cert.csv | while IFS=, read -r platform title code slug link
do
    echo "Processing $code ($slug)..."
    go run ../cmd/main.go -p amazon -s "$slug" -o "../results/raw/$code.md" -save-links "../results/saved-links/$code-link.txt" -no-cache
    sleep 3
done