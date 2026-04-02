# ExamTopics Downloader

The **ExamTopics Downloader** is a high-performance, concurrent scraping tool designed to programmatically fetch, consolidate, and export examination questions from the ExamTopics platform (which is otherwise paywalled and heavily restricted). It supports both single-exam fetching and large-scale batch processing.

## 🚀 Key Features

- **High Concurrency & Efficiency**: Uses worker pools to scrape multiple pages simultaneously to maximize throughput.
- **Smart Fetching Strategies**: 
  - **GitHub Data Cache**: Instantly retrieves previously fetched exams from a dedicated GitHub repository to avoid rate-limiting.
  - **Pre-fetched Links Caching**: For batch operations, it scans a provider's database once, drastically reducing HTTP requests and API overhead by up to 95%.
  - **Manual Fallback**: Automatically falls back to full scraping for new or uncached exams.
- **Multiple Supported Formats**: Export data cleanly into Markdown (`.md`), HTML (`.html`), PDF (`.pdf`), or Plain Text (`.txt`).
- **Comprehensive Exporter**: Captures questions, suggested answers, timestamps, and optionally, all user discussion comments.

---

## 🛠️ Setup & Installation

### Option 1: Using Docker (Recommended)

1. Ensure [Docker](https://docs.docker.com/engine/install/) is installed on your system.
2. Pull and run the image:

```bash
docker pull ghcr.io/thatonecodes/examtopics-downloader:latest

docker run -it \
  --name examtopics-downloader \
  ghcr.io/thatonecodes/examtopics-downloader:latest \
  -p google -s devops \
  -save-links -o output.md

# Extract your files
docker cp examtopics-downloader:/app/output.md .
docker cp examtopics-downloader:/app/saved-links.txt .
docker rm examtopics-downloader
```

> [!NOTE]  
> If you are on `linux/arm64` and see `exec: format exec error`, append `--platform linux/arm64` to your `docker run` command.

### Option 2: Building from Source

1. Install [Golang >= 1.24](https://go.dev/doc/install).
2. Clone the repository:
   ```bash
   git clone https://github.com/thatonecodes/examtopics-downloader.git
   cd examtopics-downloader
   ```

---

## 📖 Usage Guide

There are two primary modes of operation: **Single Exam Downloader** and **Batch Downloader**.

### 1. Single Exam Downloader (`main.go`)

Used for quickly downloading questions for a specific exam or keyword.

```bash
# Example: Download Cisco AWS 200-301 questions
go run ./cmd/main.go -p cisco -s 200-301

# Example: Get all exams from Google containing "devops"
go run ./cmd/main.go -p google -s devops
```

### 2. Batch Downloader (`process_all/main.go`)

The `process_all` module is engineered for downloading entire directories of exams from a specific provider in one execution. It completely organizes files into isolated folders (e.g., `data/amazon/`) and provides three robust ways to supply the exams list.

```bash
cd cmd/process_all
go build -o process_all .
```

#### Method A: Inline Arguments
Supply slugs directly via the CLI command.
```bash
./process_all -p google az-900 az-104 dp-203
```

#### Method B: Exam List File (`-exams`)
Pass a simple text file containing one exam slug per line.
```bash
./process_all -p google -exams ../../input/google_exams.txt
```

#### Method C: CSV Import (`-csv`)
Process large certification mappings from a structured CSV.
```bash
./process_all -p microsoft -csv ../../input/microsoft_cert.csv
```

**Output Structure Example:**
```text
data/
└── google/
    ├── associate-cloud-engineer.md
    ├── professional-data-engineer.md
    └── links/
        ├── associate-cloud-engineer-link.txt
        └── professional-data-engineer-link.txt
```

---

## ⚙️ Command Line Arguments Reference

### General Arguments (`main.go`)

| Flag | Description |
| ---- | ----------- |
| `-p` | Name of the exam provider (e.g., `google`, `amazon`, `microsoft`) |
| `-s` | Search string/slug to grep for in discussion links (required for `main.go`) |
| `-o` | Output file path (Default: `examtopics_output.md`) |
| `-type` | Output file format: `md`, `pdf`, `html`, `txt` |
| `-c` | Include community comments and discussion texts *(Boolean)* |
| `-save-links`| Save unique question source links to a text file *(Boolean)* |
| `-t` | Your GitHub Personal Access Token (PAT). Substantially increases API limits for cache retrieval |
| `-no-cache` | Disables checking the GitHub cache and forces a manual real-time scrape *(Boolean)* |
| `-exams` | Lists all available exams for the selected provider and exits |

### Batch processing Arguments (`process_all`)

| Flag | Description |
| ---- | ----------- |
| `-p` | Name of the provider |
| `-exams` | Path to a text file containing exam slugs (One per line) |
| `-csv` | Path to a CSV file containing target exams |
| `-output-dir`| Custom directory to save results. Defaults to `data/<provider>/` |
| `-sleep` | Sleep interval (in seconds) between downloading exams to prevent rate limits. Default is `3` |

---

## 🌐 Supported Providers

Check exams dynamically with `go run ./cmd/main.go -p <provider> -exams`. Supported networks include but are not limited to:

- `amazon` *(AWS)*
- `cisco`
- `comptia`
- `microsoft`
- `google`
- `salesforce`
- `vmware`
- `isaca`
- `isc2`
- `fortinet`
- `servicenow`
- `juniper`

> [!CAUTION]
> The more expansive a provider's database, the longer the manual scrape (`-no-cache`) will take. We recommend providing a `-t <GITHUB_TOKEN>` for significantly faster cache downloads.

---

## 📝 Roadmap

- [ ] Automatic JSON generation schema
- [ ] Integration of Image to Text Conversion (OCR)