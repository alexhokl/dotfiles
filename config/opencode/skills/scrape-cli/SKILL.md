---
name: scrape-cli
description: Use when the user asks to scrape article content, links, titles, or filenames from websites using the local `scrape` CLI tool. Trigger when given a URL from a supported site (theguardian.com, learn.microsoft.com, go.dev, tofugu.com, nytimes.com, tailscale.com, blog.cloudflare.com, en.wikipedia.org, ollama.com, grafana.com) and asked to extract content.
---

# scrape-cli

## Plan Mode

All `scrape` commands fetch remote web content to stdout and make no local changes —
they are **allowed in plan mode**. Writing output to a file (e.g., `> file.md`) is
**forbidden in plan mode**.

## Prerequisites

- `scrape` binary must be in PATH
  - Install from repo: `task install` (or `go install github.com/alexhokl/scrape@latest`)
  - Verify: `which scrape`

## How to Use

1. Identify the `--source` value from the URL (see Source Reference below)
2. Choose the subcommand: `article`, `links`, `title`, or `filename`
3. Execute via Bash tool, capturing stdout
4. When saving output, use the `filename` subcommand to generate a safe filename first

## Source Reference

| Source string  | Domain                    | article | links | title | filename |
|----------------|---------------------------|---------|-------|-------|----------|
| `guardian`     | `www.theguardian.com`     | yes     | yes   | yes   | yes      |
| `microsoft`    | `learn.microsoft.com`     | yes     | —     | yes   | yes      |
| `go`           | `go.dev`                  | yes     | —     | yes   | yes      |
| `tofugu`       | `www.tofugu.com`          | yes     | —     | yes   | yes      |
| `newyorktimes` | `nytimes.com`             | yes     | —     | —     | —        |
| `tailscale`    | `tailscale.com`           | yes     | —     | —     | —        |
| `cloudflare`   | `blog.cloudflare.com`     | yes     | —     | yes   | yes      |
| `wikipedia`    | `en.wikipedia.org`        | yes     | —     | yes   | yes      |
| `ollama`       | `ollama.com`              | yes     | —     | yes   | yes      |
| `grafana`      | `grafana.com`             | yes     | —     | yes   | yes      |

> **Note:** `newyorktimes` and `tailscale` only support `article`; attempting `title`
> or `filename` with those sources returns an `"invalid source"` error. Use `article`
> and extract the title from the Markdown output if needed.
>
> **Note:** `cloudflare` targets `blog.cloudflare.com` (the Ghost CMS blog), not
> `developers.cloudflare.com` (the docs site). Using the wrong domain will produce
> empty output without an error.

## Key Commands

### Scrape article body as Markdown

```bash
scrape article --source <source> -u "<url>"
```

Examples:

```bash
scrape article --source wikipedia -u "https://en.wikipedia.org/wiki/Go_(programming_language)"
scrape article --source guardian -u "https://www.theguardian.com/technology/..."
scrape article --source newyorktimes -u "https://www.nytimes.com/..."
scrape article --source go -u "https://go.dev/doc/effective_go"
```

### Scrape and save with generated filename

Use `filename` first to produce a filesystem-safe name, then write the article:

```bash
FILENAME=$(scrape filename --source <source> -u "<url>")
scrape article --source <source> -u "<url>" > "$FILENAME"
```

Example:

```bash
FILENAME=$(scrape filename --source wikipedia -u "https://en.wikipedia.org/wiki/Merkle_tree")
scrape article --source wikipedia -u "https://en.wikipedia.org/wiki/Merkle_tree" > "$FILENAME"
```

### Scrape links from a page

Only supported for `guardian`.

```bash
scrape links --source guardian -u "https://www.theguardian.com/uk"
```

Output format: one `[link text](url)` per line.

### Get article title only

```bash
scrape title --source <source> -u "<url>"
```

### Get filesystem-safe filename for an article

```bash
scrape filename --source <source> -u "<url>"
```

## Common Workflows

### Scrape article to clipboard (macOS)

```bash
scrape article --source microsoft -u "https://learn.microsoft.com/..." | pbcopy
```

### Scrape multiple articles listed on a Guardian page

```bash
# Step 1: collect links
scrape links --source guardian -u "https://www.theguardian.com/uk" > links.txt

# Step 2: for each article URL, scrape and save using the generated filename
grep -oP 'https://[^)]+' links.txt | while IFS= read -r url; do
  filename=$(scrape filename --source guardian -u "$url")
  scrape article --source guardian -u "$url" > "$filename"
done
```

### Determine the correct source from a URL

Match the URL hostname to the Source Reference table above. When the hostname is
ambiguous or not listed, do not guess — inform the user that the URL is not supported.
