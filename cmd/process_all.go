package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"examtopics-downloader/internal/fetch"
	"examtopics-downloader/internal/models"
	"examtopics-downloader/internal/utils"
)

func main() {
	csvFile := flag.String("csv", "../src/microsoft_cert.csv", "Path to the CSV file containing certification data")
	provider := flag.String("p", "microsoft", "Name of the exam provider")
	outputDir := flag.String("output-dir", "../results/raw", "Directory to save output files")
	saveLinksDir := flag.String("links-dir", "../results/saved-links", "Directory to save links files")
	commentBool := flag.Bool("c", false, "Optionally include all the comment/discussion text")
	fileType := flag.String("type", "md", "Optionally include file type (default -> .md)")
	noCache := flag.Bool("no-cache", false, "Optional argument, set to disable looking through cached data on github")
	token := flag.String("t", "", "Optional argument to make cached requests faster to gh api")
	sleepTime := flag.Int("sleep", 3, "Sleep time in seconds between each certification processing")
	flag.Parse()

	// Read CSV file
	file, err := os.Open(*csvFile)
	if err != nil {
		log.Fatalf("Error opening CSV file: %v", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil {
		log.Fatalf("Error reading CSV file: %v", err)
	}

	// Skip header row
	if len(records) < 2 {
		log.Fatal("CSV file is empty or has no data rows")
	}

	// Create output directories if they don't exist
	os.MkdirAll(*outputDir, 0755)
	os.MkdirAll(*saveLinksDir, 0755)

	// Process each certification
	totalCerts := len(records) - 1
	for i, record := range records[1:] {
		if len(record) < 4 {
			log.Printf("Skipping invalid record at line %d", i+2)
			continue
		}

		// Extract fields from CSV
		// platform := record[0]
		// title := record[1]
		code := record[2]
		slug := record[3]
		// link := record[4]

		fmt.Printf("\n[%d/%d] Processing %s (%s)...\n", i+1, totalCerts, code, slug)

		// Prepare output paths
		outputPath := filepath.Join(*outputDir, code+"."+*fileType)
		linksPath := filepath.Join(*saveLinksDir, code+"-link.txt")

		// Fetch data
		var questionData []models.QuestionData
		if !*noCache {
			questionData = fetch.GetCachedPages(*provider, slug, *token)
			if len(questionData) > 0 {
				fmt.Printf("Found cached data for %s\n", code)
			}
		}

		if len(questionData) == 0 {
			fmt.Printf("Fetching data manually for %s...\n", code)
			questionData = fetch.GetAllPages(*provider, slug)
		}

		if len(questionData) == 0 {
			log.Printf("Warning: No data found for %s (%s)", code, slug)
			continue
		}

		// Save links
		utils.SaveLinks(linksPath, questionData)

		// Write data to output file
		utils.WriteData(questionData, outputPath, *commentBool, *fileType)
		fmt.Printf("Successfully saved output to %s (filetype: %s)\n", outputPath, *fileType)

		// Sleep between requests to avoid rate limiting
		if i < totalCerts-1 {
			fmt.Printf("Sleeping for %d seconds...\n", *sleepTime)
			time.Sleep(time.Duration(*sleepTime) * time.Second)
		}
	}

	fmt.Printf("\n✅ Processing complete! Processed %d certifications.\n", totalCerts)
}
