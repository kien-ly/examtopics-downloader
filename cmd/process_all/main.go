package main

import (
	"bufio"
	"encoding/csv"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	"examtopics-downloader/internal/fetch"
	"examtopics-downloader/internal/models"
	"examtopics-downloader/internal/utils"
)

type certRecord struct {
	Code string
	Slug string
}

// loadCertsFromCSV reads a full CSV file (with header).
// CSV columns: Platform, Title, Code, Slug, Link
func loadCertsFromCSV(path string) ([]certRecord, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("cannot open CSV: %w", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil {
		return nil, fmt.Errorf("cannot read CSV: %w", err)
	}

	if len(records) < 2 {
		return nil, fmt.Errorf("CSV file is empty or has no data rows")
	}

	var certs []certRecord
	for i, record := range records[1:] {
		if len(record) < 4 {
			log.Printf("Skipping invalid CSV record at line %d", i+2)
			continue
		}
		code := strings.TrimSpace(record[2])
		slug := strings.TrimSpace(record[3])
		if code == "" || slug == "" {
			log.Printf("Skipping CSV record at line %d: empty code or slug", i+2)
			continue
		}
		certs = append(certs, certRecord{Code: code, Slug: slug})
	}
	return certs, nil
}

// loadCertsFromExamList reads a simple text file with one exam slug per line.
// Lines starting with # are comments. Empty lines are skipped.
// Format: slug (code defaults to slug if not specified)
//
//	slug:code (optional explicit code)
func loadCertsFromExamList(path string) ([]certRecord, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("cannot open exam list: %w", err)
	}
	defer file.Close()

	var certs []certRecord
	scanner := bufio.NewScanner(file)
	lineNum := 0
	for scanner.Scan() {
		lineNum++
		line := strings.TrimSpace(scanner.Text())

		// Skip empty lines and comments
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		// Support format: slug or slug:code
		parts := strings.SplitN(line, ":", 2)
		slug := strings.TrimSpace(parts[0])
		code := slug // default code = slug
		if len(parts) == 2 {
			code = strings.TrimSpace(parts[1])
		}

		if slug == "" {
			log.Printf("Skipping empty slug at line %d", lineNum)
			continue
		}

		certs = append(certs, certRecord{Code: code, Slug: slug})
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("error reading exam list: %w", err)
	}
	return certs, nil
}

// parseCertsFromArgs reads exam slugs from CLI positional arguments.
// Usage: process_all -p google az-900 az-104 dp-203
func parseCertsFromArgs(args []string) []certRecord {
	var certs []certRecord
	for _, arg := range args {
		slug := strings.TrimSpace(arg)
		if slug == "" {
			continue
		}
		certs = append(certs, certRecord{Code: slug, Slug: slug})
	}
	return certs
}

func main() {
	csvFile := flag.String("csv", "", "Path to CSV file (columns: Platform,Title,Code,Slug,Link)")
	examList := flag.String("exams", "", "Path to exam list file (one slug per line)")
	provider := flag.String("p", "microsoft", "Name of the exam provider (google, amazon, microsoft, ...)")
	outputDir := flag.String("output-dir", "", "Directory to save output files (default: data/<provider>)")
	saveLinksDir := flag.String("links-dir", "", "Directory to save links files (default: data/<provider>/links)")
	commentBool := flag.Bool("c", false, "Include all comment/discussion text")
	fileType := flag.String("type", "md", "Output file type: md, pdf, html, text")
	noCache := flag.Bool("no-cache", false, "Disable cached data lookup on GitHub")
	token := flag.String("t", "", "GitHub API token for faster cached requests")
	sleepTime := flag.Int("sleep", 3, "Sleep time in seconds between exams")
	flag.Parse()

	// ── Load cert list from one of 3 sources ──
	var certs []certRecord
	var err error

	switch {
	case *csvFile != "":
		// Source 1: Full CSV file
		certs, err = loadCertsFromCSV(*csvFile)
		if err != nil {
			log.Fatalf("Error loading CSV: %v", err)
		}
		fmt.Printf("📄 Loaded %d exams from CSV: %s\n", len(certs), *csvFile)

	case *examList != "":
		// Source 2: Simple exam list file
		certs, err = loadCertsFromExamList(*examList)
		if err != nil {
			log.Fatalf("Error loading exam list: %v", err)
		}
		fmt.Printf("📄 Loaded %d exams from list: %s\n", len(certs), *examList)

	case flag.NArg() > 0:
		// Source 3: CLI positional arguments
		certs = parseCertsFromArgs(flag.Args())
		fmt.Printf("📄 Loaded %d exams from arguments\n", len(certs))

	default:
		fmt.Println("Usage: process_all -p <provider> [options] [exam-slugs...]")
		fmt.Println()
		fmt.Println("Input sources (pick one):")
		fmt.Println("  process_all -p google az-900 az-104         # inline exam slugs")
		fmt.Println("  process_all -p google -exams exams.txt      # from exam list file")
		fmt.Println("  process_all -p microsoft -csv certs.csv     # from full CSV file")
		fmt.Println()
		flag.PrintDefaults()
		os.Exit(1)
	}

	if len(certs) == 0 {
		log.Fatal("No valid exams found in input")
	}

	// ── Default output paths: ../../data/<provider>/ ──
	if *outputDir == "" {
		*outputDir = filepath.Join("../../data", *provider)
	}
	if *saveLinksDir == "" {
		*saveLinksDir = filepath.Join("../../data", *provider, "links")
	}

	if err := os.MkdirAll(*outputDir, 0755); err != nil {
		log.Fatalf("Error creating output directory %s: %v", *outputDir, err)
	}
	if err := os.MkdirAll(*saveLinksDir, 0755); err != nil {
		log.Fatalf("Error creating links directory %s: %v", *saveLinksDir, err)
	}

	// ── Pre-fetch all provider discussion links (one-time) ──
	var allProviderLinks []string

	if *noCache {
		fmt.Printf("\n🔍 Fetching all discussion links for provider '%s' (one-time scan)...\n", *provider)
		linksBySlug, err := fetch.GetAllLinksForProvider(*provider)
		if err != nil {
			log.Fatalf("Error fetching provider links: %v", err)
		}
		allProviderLinks = linksBySlug[""]
		fmt.Printf("   Total links found: %d\n", len(allProviderLinks))
	}

	// ── Process each exam ──
	totalCerts := len(certs)
	successCount := 0
	failCount := 0
	cachedCount := 0

	fmt.Printf("\n🚀 Processing %d exam(s) for provider '%s'...\n", totalCerts, *provider)

	for i, cert := range certs {
		fmt.Printf("\n[%d/%d] Processing %s (%s)...\n", i+1, totalCerts, cert.Code, cert.Slug)

		outputPath := filepath.Join(*outputDir, cert.Code+"."+*fileType)
		linksPath := filepath.Join(*saveLinksDir, cert.Code+"-link.txt")

		var questionData []models.QuestionData

		// Strategy 1: Try GitHub cache
		if !*noCache {
			questionData = fetch.GetCachedPages(*provider, cert.Slug, *token)
			if len(questionData) > 0 {
				fmt.Printf("   ✓ Found cached data (%d questions)\n", len(questionData))
				cachedCount++
			}
		}

		// Strategy 2: Use pre-fetched links (filtered by slug)
		if len(questionData) == 0 && len(allProviderLinks) > 0 {
			filteredLinks := fetch.FilterLinksBySlug(allProviderLinks, cert.Slug)
			if len(filteredLinks) > 0 {
				fmt.Printf("   ↳ Scraping %d pre-fetched links...\n", len(filteredLinks))
				questionData = fetch.ScrapeLinks(filteredLinks)
			}
		}

		// Strategy 3: Full manual fetch (fallback)
		if len(questionData) == 0 {
			fmt.Printf("   ↳ Full manual fetch...\n")
			questionData = fetch.GetAllPages(*provider, cert.Slug)
		}

		if len(questionData) == 0 {
			log.Printf("   ✗ No data found for %s (%s)", cert.Code, cert.Slug)
			failCount++
			continue
		}

		utils.SaveLinks(linksPath, questionData)
		utils.WriteData(questionData, outputPath, *commentBool, *fileType, true)
		fmt.Printf("   ✓ Saved %d questions → %s\n", len(questionData), outputPath)
		successCount++

		if i < totalCerts-1 && *sleepTime > 0 {
			fmt.Printf("   ⏳ Sleeping %ds...\n", *sleepTime)
			time.Sleep(time.Duration(*sleepTime) * time.Second)
		}
	}

	fmt.Printf("\n" + strings.Repeat("─", 50) + "\n")
	fmt.Printf("✅ Processing complete!\n")
	fmt.Printf("   Total: %d | Success: %d | Failed: %d | Cached: %d\n",
		totalCerts, successCount, failCount, cachedCount)
	fmt.Printf("   Output: %s\n", *outputDir)
}
