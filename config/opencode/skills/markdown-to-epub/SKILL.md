---
name: markdown-to-epub
description: Use when the user asks to convert a Markdown (.md) file to EPUB format using the markdown-to-epub CLI. Trigger when given a .md file and asked to produce an .epub output, or when asked to run markdown-to-epub generate.
---

# markdown-to-epub

Converts a Markdown file to an EPUB e-book using the `markdown-to-epub generate` subcommand.

## Plan / Ask Mode (Read-Only)

Before executing any command, check whether a `<system-reminder>` block containing
`Plan mode ACTIVE` is present in your current context. If it is, you are in
**read-only mode** and MUST NOT write any files to disk.

**Forbidden in read-only mode:**
- `markdown-to-epub generate ...` (produces an `.epub` output file)
- Any invocation that writes or overwrites a file

**Allowed in read-only mode:**
- `markdown-to-epub --help`
- `markdown-to-epub generate --help`
- `which markdown-to-epub`

If the user requests a conversion while in read-only mode, respond:
> "I am currently in plan/read-only mode. I can describe what this operation would do, but I will not write files until plan mode ends."

## Prerequisites

Verify the binary is installed before invoking it:

```bash
which markdown-to-epub
```

If not found, install it:

```bash
go install github.com/alexhokl/markdown-to-epub@latest
```

## Flag Reference

All flags belong to the `generate` subcommand.

| Flag          | Short | Required | Default          | Description                                  |
|---------------|-------|----------|------------------|----------------------------------------------|
| `--input`     | `-i`  | yes      | —                | Path to the source Markdown file             |
| `--output`    | `-o`  | yes      | —                | Path for the output EPUB file                |
| `--overwrite` | `-f`  | no       | `false`          | Overwrite the output file if it already exists |
| `--title`     | `-t`  | no       | first `# H1`     | EPUB title metadata                          |
| `--author`    | `-a`  | no       | —                | EPUB author metadata                         |
| `--language`  | `-l`  | no       | `en`             | BCP 47 language code for the EPUB            |

## Key Commands

### Minimal conversion (title auto-detected from first `# H1`)

```bash
markdown-to-epub generate -i input.md -o output.epub
```

### Full conversion with explicit metadata

```bash
markdown-to-epub generate -i input.md -o output.epub \
  -t "My Book Title" \
  -a "Author Name" \
  -l en
```

### Overwrite an existing output file

```bash
markdown-to-epub generate -i input.md -o output.epub -f
```

## Common Workflows

### Basic conversion

```bash
markdown-to-epub generate -i document.md -o document.epub
```

### Derive the output filename from the input filename

```bash
markdown-to-epub generate -i notes.md -o notes.epub
```

### Japanese-language document

```bash
markdown-to-epub generate -i book.md -o book.epub -l ja
```

### Add author metadata

```bash
markdown-to-epub generate -i report.md -o report.epub -a "Jane Smith"
```

### Explicit title (overrides the first `# H1` heading)

```bash
markdown-to-epub generate -i draft.md -o draft.epub -t "Final Title"
```

### Re-generate and overwrite after editing the source

```bash
markdown-to-epub generate -i chapter.md -o chapter.epub -f
```

## Notes

- **Title auto-detection** — if `--title` is omitted, the tool extracts the text
  of the first `# H1` heading in the Markdown file. If no `# H1` is found, it
  falls back to the input filename stem.
- **Relative image paths** — relative `<img src>` paths in the Markdown are
  resolved relative to the directory of the input file. Remote image URLs are
  downloaded automatically using a `markdown-to-epub/1.0` User-Agent header.
- **Language codes** — use BCP 47 codes: `en` (English), `ja` (Japanese),
  `zh` (Chinese), `fr` (French), `de` (German), etc.
- **Output file guard** — without `-f`, the command exits with an error if the
  output file already exists. Always pass `-f` when re-generating.
- **CSS styling** — the EPUB is styled with an embedded `style.css`; no external
  stylesheet is required.
