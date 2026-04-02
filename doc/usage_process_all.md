# Hướng dẫn sử dụng `process_all`

> Batch download exam questions từ ExamTopics theo provider.

---

## Build

```bash
cd cmd/process_all
go build -o process_all .
```

---

## 3 cách nhập danh sách exam

### Cách 1: Inline — gõ trực tiếp trên CLI (nhanh nhất)

```bash
./process_all -p google az-900 az-104 dp-203
```

Mỗi argument sau flags là 1 exam slug. Code mặc định = slug.

### Cách 2: Exam list file — file text đơn giản (`-exams`)

```bash
./process_all -p google -exams ../../input/google_exams.txt
```

**Format file:**
```text
# Comment (bỏ qua)
# Dòng trống cũng bỏ qua

# Chỉ slug (code = slug)
associate-cloud-engineer
professional-data-engineer

# Slug + code tùy chỉnh (slug:code)
saa-c03:SAA-C03
clf-c02:CLF-C02
```

**Ví dụ files có sẵn:**
- `examples/google_exams.txt` — Google Cloud
- `examples/amazon_exams.txt` — Amazon AWS

### Cách 3: Full CSV (`-csv`)

```bash
./process_all -p microsoft -csv ../../input/microsoft_cert.csv
```

**Format CSV** (có header row):
```csv
Platform,Certification Title,Certification Code,Certification Slug,Certification link
Microsoft,Microsoft AZ-900,AZ-900,az-900,https://www.examtopics.com/exams/microsoft/az-900/
Microsoft,Microsoft AZ-104,AZ-104,az-104,https://www.examtopics.com/exams/microsoft/az-104/
```

Cột quan trọng: `Code` (cột 3) và `Slug` (cột 4).

---

## Cấu trúc output

```
data/
├── google/
│   ├── associate-cloud-engineer.md
│   ├── professional-data-engineer.md
│   └── links/
│       ├── associate-cloud-engineer-link.txt
│       └── professional-data-engineer-link.txt
├── amazon/
│   ├── SAA-C03.md
│   └── links/
│       └── SAA-C03-link.txt
└── microsoft/
    ├── AZ-900.md
    └── links/
        └── AZ-900-link.txt
```

---

## Tất cả flags

| Flag | Default | Mô tả |
|------|---------|-------|
| `-p` | `microsoft` | Tên provider (google, amazon, microsoft, lpi, ...) |
| `-exams` | | File danh sách exam (text, mỗi dòng 1 slug) |
| `-csv` | | File CSV đầy đủ (5 cột, có header) |
| `-output-dir` | `data/<provider>` | Thư mục output |
| `-links-dir` | `data/<provider>/links` | Thư mục lưu links |
| `-type` | `md` | Loại file output: `md`, `pdf`, `html`, `text` |
| `-c` | `false` | Bao gồm phần discussion/comments |
| `-no-cache` | `false` | Bỏ qua cache GitHub, scrape trực tiếp |
| `-t` | | GitHub token (tăng tốc khi dùng cache) |
| `-sleep` | `3` | Thời gian chờ giữa các exam (giây) |

---

## Ví dụ thực tế

### Download 2 exam Google Cloud, output markdown

```bash
./process_all -p google associate-cloud-engineer professional-data-engineer
```

### Download từ file, bao gồm comments, output PDF

```bash
./process_all -p amazon -exams ../../examples/amazon_exams.txt -c -type pdf
```

### Download toàn bộ Microsoft cert từ CSV, không dùng cache

```bash
./process_all -p microsoft -csv ../../src/microsoft_cert.csv -no-cache
```

### Download nhanh 1 exam có token GitHub

```bash
./process_all -p google -t ghp_xxxxx professional-cloud-architect
```

### Custom output directory

```bash
./process_all -p google -output-dir ./my-results associate-cloud-engineer
```

---

## Thứ tự chiến lược fetch data

Với mỗi exam, chương trình thử theo thứ tự:

1. **GitHub Cache** — nhanh nhất, dùng data cached sẵn trên repo
2. **Pre-fetched links** — fetch TẤT CẢ discussion 1 lần, lọc theo slug (chỉ khi `-no-cache`)
3. **Manual scrape** — fallback, fetch riêng cho exam đó

```
[1/3] Processing AZ-900 (az-900)...
   ✓ Found cached data (120 questions)       ← Strategy 1
   ✓ Saved 120 questions → data/microsoft/AZ-900.md

[2/3] Processing AZ-104 (az-104)...
   ↳ Scraping 85 pre-fetched links...        ← Strategy 2
   ✓ Saved 85 questions → data/microsoft/AZ-104.md

[3/3] Processing DP-203 (dp-203)...
   ↳ Full manual fetch...                    ← Strategy 3
   ✓ Saved 60 questions → data/microsoft/DP-203.md

──────────────────────────────────────────────────
✅ Processing complete!
   Total: 3 | Success: 3 | Failed: 0 | Cached: 1
   Output: data/microsoft
```
