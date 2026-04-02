# Ghi chú tối ưu cho `cmd/process_all.go`

> Phân tích dựa trên toàn bộ codebase: `cmd/`, `internal/`, `tests/`, `go.mod`

---

## 1. 🔥 Quét lại toàn bộ discussion pages cho MỖI exam — lãng phí nghiêm trọng

**Mức độ:** 🔴 Nghiêm trọng — Lãng phí ~95% requests, chậm gấp N lần  
**Vị trí:** `process_all.go:83` → `fetch.GetAllPages()` → `scraper.go:160-213`

**Luồng hiện tại (mỗi exam trong vòng lặp CSV):**

```
Exam AZ-104 → GetAllPages("microsoft", "az-104")
  → getMaxNumPages("https://www.examtopics.com/discussions/microsoft/")
    → Tìm thấy 500 pages
  → fetchAllPageLinksConcurrently("microsoft", "az-104", 500, 15)
    → Fetch TẤT CẢ 500 pages, grep link chứa "az-104"
    → Tìm thấy 80 links → scrape 80 links

Exam AZ-900 → GetAllPages("microsoft", "az-900")
  → getMaxNumPages(...)  → LẠI 500 pages (CÙNG 500 pages!)
  → fetchAllPageLinksConcurrently("microsoft", "az-900", 500, 15)
    → LẠI fetch TẤT CẢ 500 pages → lọc link chứa "az-900"
```

**Vấn đề:** 20 exam Microsoft → `500 × 20 = 10,000 page requests`, thực tế chỉ cần **500**.

**Đề xuất — Fetch 1 lần, lọc nhiều lần:**

```go
// Bước 1: Fetch tất cả links của provider 1 lần duy nhất
func GetAllLinksForProvider(providerName string) map[string][]string {
    baseURL := fmt.Sprintf("https://www.examtopics.com/discussions/%s/", providerName)
    numPages := getMaxNumPages(baseURL)
    allLinks := fetchAllPageLinksConcurrently(providerName, "", numPages, ...)

    // Phân loại links theo exam slug
    linksBySlug := make(map[string][]string)
    for _, link := range allLinks {
        for _, slug := range knownSlugs {
            if strings.Contains(link, slug) {
                linksBySlug[slug] = append(linksBySlug[slug], link)
            }
        }
    }
    return linksBySlug
}

// Bước 2 (process_all.go): Loop qua từng cert, chỉ scrape links tương ứng
allLinks := fetch.GetAllLinksForProvider(*provider)
for _, record := range records[1:] {
    links := allLinks[record[3]]
    questionData := fetch.ScrapeLinks(links)
}
```

**Hiệu quả:** `N × totalPages` requests → `totalPages + matchedLinks` requests.

---

## 2. 🔥 Biến global `counter` — sai số thứ tự câu hỏi khi chạy batch

**Mức độ:** 🔴 Nghiêm trọng — Data output sai  
**Vị trí:** `internal/fetch/scraper.go:50`

```go
var counter int = 0 // biến GLOBAL, không bao giờ reset
```

Khi `process_all.go` chạy loop nhiều exam:
- Exam 1 (50 câu): `#1` → `#50` ✅
- Exam 2 (30 câu): `#51` → `#80` ❌ (phải là `#1` → `#30`)

**Đề xuất:** Bỏ global counter, truyền index qua tham số:

```go
func getJSONFromLink(link string, startIndex int) []*models.QuestionData {
    for i, q := range content.PageProps.Questions {
        title := fmt.Sprintf("question #%d", startIndex+i+1)
    }
}
```

---

## 3. Hai file `main.go` cùng `package main` — xung đột build

**Mức độ:** 🔴 Cao — Không build được  
**Vị trí:** `cmd/main.go` và `cmd/process_all.go`

Cả hai đều có `func main()` trong cùng 1 package. Go không cho phép điều này.

**Đề xuất:** Tách thành 2 command riêng:
```
cmd/
├── downloader/main.go       # cmd hiện tại
└── process_all/main.go      # cmd batch processing
```

---

## 4. Không xử lý lỗi `os.MkdirAll`

**Mức độ:** 🔴 Cao — Bug ẩn, khó debug  
**Vị trí:** `process_all.go:48-49`

```go
// ❌ Hiện tại
os.MkdirAll(*outputDir, 0755)

// ✅ Đề xuất
if err := os.MkdirAll(*outputDir, 0755); err != nil {
    log.Fatalf("Error creating output directory: %v", err)
}
```

---

## 5. `deleteMarkdownFile()` treo chương trình khi chạy batch

**Mức độ:** 🔴 Cao — Block chương trình  
**Vị trí:** `internal/utils/files.go:134-146`

`WriteData()` gọi `deleteMarkdownFile()` khi output type là `pdf`/`html`/`text`. Hàm này **chờ user nhập y/n từ stdin** cho MỖI cert → 50+ cert = 50+ lần chờ.

**Đề xuất:** Thêm tham số `autoDelete bool` vào `WriteData()` hoặc flag `--auto-delete`.

---

## 6. Thiếu concurrency ở cấp cert

**Mức độ:** 🟡 Trung bình — Chạy chậm  
**Vị trí:** `process_all.go:53-103`

Vòng lặp xử lý tuần tự 1 cert/lần, trong khi `GetCachedPages()` bên trong đã có goroutine.

**Đề xuất:** Dùng worker pool:

```go
sem := make(chan struct{}, 5)
var wg sync.WaitGroup
for i, record := range records[1:] {
    wg.Add(1)
    sem <- struct{}{}
    go func(i int, record []string) {
        defer wg.Done()
        defer func() { <-sem }()
        // process cert...
    }(i, record)
}
wg.Wait()
```

> **Lưu ý:** Cần thay `time.Sleep` bằng rate limiter (`golang.org/x/time/rate`).

---

## 7. Thiếu graceful shutdown (Ctrl+C)

**Mức độ:** 🟡 Trung bình — Có thể gây data corruption  
**Vị trí:** `process_all.go` — toàn file

Nhấn `Ctrl+C` khi đang xử lý → file output bị ghi dở.

**Đề xuất:**
```go
ctx, cancel := context.WithCancel(context.Background())
sigChan := make(chan os.Signal, 1)
signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
go func() {
    <-sigChan
    fmt.Println("\n⚠️ Shutting down gracefully...")
    cancel()
}()
```

---

## 8. CSV validation yếu

**Mức độ:** 🟡 Trung bình — Runtime error  
**Vị trí:** `process_all.go:54-57`

Chỉ kiểm tra `len(record) < 4`, không validate nội dung.

**Đề xuất:**
```go
code := strings.TrimSpace(record[2])
slug := strings.TrimSpace(record[3])
if code == "" || slug == "" {
    log.Printf("Skipping record at line %d: empty code or slug", i+2)
    continue
}
```

---

## 9. Chưa dùng progress bar (đã có dependency)

**Mức độ:** 🟢 Thấp — UX  
**Vị trí:** `process_all.go:66`

`go.mod` đã có `github.com/cheggaaa/pb/v3` nhưng `process_all.go` chỉ dùng `fmt.Printf`.

**Đề xuất:**
```go
bar := pb.StartNew(totalCerts)
defer bar.Finish()
// trong loop:
bar.Increment()
```

---

## 10. Thiếu summary thống kê cuối cùng

**Mức độ:** 🟢 Thấp — UX  
**Vị trí:** `process_all.go:105`

**Đề xuất:** Thêm thống kê chi tiết:
```go
fmt.Printf("Total: %d | Success: %d | Failed: %d | Cached: %d\n",
    total, success, failed, cached)
```

---

## 11. Sleep time cứng

**Mức độ:** 🟢 Thấp — Linh hoạt  
**Vị trí:** `process_all.go:101`

Nên cho phép giá trị `0` để disable sleep và log rõ ràng hơn.

---

## Bảng tóm tắt

| # | Vấn đề | Mức độ | Ảnh hưởng |
|---|--------|--------|-----------|
| 1 | Quét lại toàn bộ pages cho mỗi exam | 🔴 Nghiêm trọng | Lãng phí 95% requests |
| 2 | Global counter sai số thứ tự | 🔴 Nghiêm trọng | Data sai khi batch |
| 3 | Xung đột 2 `main()` | 🔴 Cao | Không build được |
| 4 | Bỏ qua lỗi `MkdirAll` | 🔴 Cao | Bug ẩn |
| 5 | `deleteMarkdownFile` treo batch | 🔴 Cao | Block chương trình |
| 6 | Thiếu concurrency cấp cert | 🟡 Trung bình | Chạy chậm |
| 7 | Thiếu graceful shutdown | 🟡 Trung bình | Data corruption |
| 8 | CSV validation yếu | 🟡 Trung bình | Runtime error |
| 9 | Chưa dùng progress bar | 🟢 Thấp | UX |
| 10 | Thiếu summary thống kê | 🟢 Thấp | UX |
| 11 | Sleep time cứng | 🟢 Thấp | Linh hoạt |
