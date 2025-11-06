# Build stage
FROM golang:1.24 AS builder

WORKDIR /app

COPY go.mod ./
COPY go.sum ./
RUN go mod download

COPY . ./

RUN go build -o process_all ./cmd/process_all.go

FROM debian:bookworm-slim

WORKDIR /app

# Install CA certs
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /app/results/raw /app/results/saved-links && chmod -R 777 /app/results

COPY --from=builder /app/process_all .
COPY src/microsoft_cert.csv ./src/microsoft_cert.csv

ENTRYPOINT ["./process_all"]