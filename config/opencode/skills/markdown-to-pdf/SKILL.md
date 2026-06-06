---
name: markdown-to-pdf
description: Use when the user asks to convert a Markdown (.md) file to PDF format using the markdown-to-pdf CLI. Trigger when given a .md file and asked to produce a .pdf output, or when asked to run markdown-to-pdf generate.
---

# markdown-to-pdf

Converts a Markdown file to a PDF document using the `markdown-to-pdf generate` subcommand.

## Plan / Ask Mode (Read-Only)

Before executing any command, check whether a `<system-reminder>` block containing
`Plan mode ACTIVE` is present in your current context. If it is, you are in
**read-only mode** and MUST NOT write any files to disk.

**Forbidden in read-only mode:**
- `markdown-to-pdf generate ...` (produces a `.pdf` output file)
- Any invocation that writes or overwrites a file

**Allowed in read-only mode:**
- `markdown-to-pdf --help`
- `markdown-to-pdf generate --help`
- `which markdown-to-pdf`

If the user requests a conversion while in read-only mode, respond:
> "I am currently in plan/read-only mode. I can describe what this operation would do,
> but I will not write files until plan mode ends."

## Prerequisites

Verify the binary is installed before invoking it:

```bash
which markdown-to-pdf
```

If not found, install it:

```bash
go install github.com/alexhokl/markdown-to-pdf@latest
```

Or, from the repository root:

```bash
task install
```

## Flag Reference

All flags belong to the `generate` subcommand.

| Flag          | Short | Required | Default                        | Description                                    |
|---------------|-------|----------|--------------------------------|------------------------------------------------|
| `--input`     | `-i`  | yes      | —                              | Path to the source Markdown file               |
| `--output`    | `-o`  | yes      | —                              | Path for the output PDF file                   |
| `--overwrite` | `-f`  | no       | `false`                        | Overwrite the output file if it already exists |
| `--title`     | `-t`  | no       | first `# H1`, or filename stem | Title shown on the cover page                  |
| `--author`    | `-a`  | no       | —                              | Author name shown on the cover page            |
| `--language`  | `-l`  | no       | `en`                           | Language code for font selection               |
| `--font`      | —     | no       | —                              | Absolute path to a custom TTF font file        |

Supported `--language` codes: `en`, `ja`, `zh`, `zh-TW`, `zh-HK`, `ko`.

## Key Commands

### 1. Minimal conversion (title auto-detected from first `# H1`)

```bash
markdown-to-pdf generate -i input.md -o output.pdf
```

### 2. Full conversion with explicit metadata

```bash
markdown-to-pdf generate -i input.md -o output.pdf \
  -t "Document Title" \
  -a "Author Name" \
  -l en
```

### 3. CJK language document

```bash
markdown-to-pdf generate -i document.md -o document.pdf -l ja
```

The tool automatically searches system font directories for a matching CJK font
(e.g., NotoSansJP on macOS). If none is found, it prints a Homebrew install hint:

```bash
brew install --cask font-noto-sans-jp
```

### 4. Custom font

```bash
markdown-to-pdf generate -i input.md -o output.pdf --font /path/to/font.ttf
```

## Common Workflows

### Re-generate and overwrite after editing the source

```bash
markdown-to-pdf generate -i input.md -o output.pdf -f
```

### Derive the output filename from the input filename

```bash
markdown-to-pdf generate -i notes.md -o notes.pdf
```

### Japanese document with auto-discovered system font

```bash
# Install the font once if not present
brew install --cask font-noto-sans-jp

markdown-to-pdf generate -i document.md -o document.pdf -l ja
```

### Add author and explicit title

```bash
markdown-to-pdf generate -i report.md -o report.pdf \
  -t "Q2 Report" \
  -a "Jane Smith"
```

## Notes

- **Title auto-detection** — if `--title` is omitted, the tool extracts the text of
  the first `# H1` heading in the Markdown source. If no `# H1` is found, it falls
  back to the input filename without its extension.
- **Cover page always generated** — page 1 is always a cover page showing the title
  (and author if provided). There is no flag to suppress it.
- **Inline formatting is flattened** — `**bold**`, `_italic_`, `[links](url)`, and
  `` `inline code` `` are all rendered as plain text. Only block-level elements
  (headings, paragraphs, code blocks, blockquotes, lists, tables, `<hr>`) are
  structurally rendered.
- **Emoji silent substitution** — approximately 120 Unicode emoji are automatically
  replaced with ASCII equivalents (e.g., `✅` → `[v]`, `🚀` → `[rocket]`) before
  rendering. This behaviour cannot be disabled.
- **CJK font auto-discovery** — for `-l ja`, `-l zh`, `-l ko`, etc., the tool walks
  system font directories (including `/opt/homebrew/share/fonts` on macOS). If no
  suitable TrueType font is found, rendering continues with Helvetica and CJK
  characters will not display correctly.
- **Output file guard** — without `-f`, the command exits with an error if the output
  file already exists. Always pass `-f` when re-generating.
