---
name: litparse
description: Use when the user asks to read, parse, extract text, or analyze binary documents (PDF, DOCX, PPTX, XLSX) or images. Useful for spatial layout analysis or screenshot generation via lit.
---

# LiteParse Skill

This skill enables `opencode` to parse, extract text, and analyze binary documents (PDF, DOCX, PPTX, XLSX) and images locally using the `lit` CLI tool (LiteParse).

## Plan / Ask Mode (Read-Only)

Before executing any command, check whether a `<system-reminder>` block containing `Plan mode ACTIVE` is present in your current context. If it is, you are in **read-only mode** and MUST NOT write any output files to disk.

**Forbidden in read-only mode:**
- `lit parse <file> -o <output>` or `lit parse <file> --output <path>` (writing parsed output to a file)
- `lit screenshot <file> -o <dir>` (writing screenshot images to disk)
- Any invocation that persists results outside the current process

**Allowed in read-only mode:**
- `lit parse <file>` (stdout only — no `-o` / `--output` flag)
- `lit parse <file> --format json` (stdout only)
- `lit parse <file> --target-pages "..."` (stdout only)

If the user requests an output-writing operation while in read-only mode, respond:
> "I am currently in plan/read-only mode. I can describe what this operation would do, but I will not write files until plan mode ends."

## When to use this skill
- The user asks to read, parse, or extract text from a PDF, Word document, PowerPoint, Excel spreadsheet, or image.
- The user asks to analyze the layout, bounding boxes, or structure of a document.
- The user asks to convert a document's pages into screenshots for visual analysis.

## Verification
Before using `lit`, always verify it is installed by running:
```bash
which lit
```
If it is not installed, inform the user they need to install it. Common installation methods:
- Node.js: `npm i -g @llamaindex/liteparse`
- Python: `pip install liteparse`
- Rust: `cargo install liteparse`

## Common Workflows

### 1. Basic Text Extraction
Use this to quickly read the text contents of a document to answer general questions.
```bash
lit parse <file.pdf>
```

### 2. Structured Data Extraction (JSON)
Use this when you need precise bounding boxes for spatial layout analysis (e.g., extracting dense tables or understanding structural hierarchy).
```bash
lit parse <file.pdf> --format json -o output.json
```

### 3. Extracting Specific Pages
To avoid overwhelming the context window with massive documents, target specific pages if the user only needs a section.
```bash
lit parse <file.pdf> --target-pages "1-5,10"
```

### 4. Generating Screenshots
Use this if the document contains charts, graphs, handwritten notes, or visual elements that require image/vision analysis.
```bash
lit screenshot <file.pdf> -o ./screenshots
```
*Note: Once generated, you can use the `read` tool on the resulting PNG files to analyze them visually if your model supports it.*

### 5. Fast Mode (No OCR)
If you know the document is a native digital PDF (not a scanned image) and speed is crucial, you can disable the built-in OCR engine:
```bash
lit parse <file.pdf> --no-ocr
```

## Important Notes
- The actual CLI command used is `lit`, **not** `liteparse`.
- Input conversion: LiteParse supports passing `.docx`, `.pptx`, `.xlsx`, and images (e.g. `.png`, `.jpg`) directly to the `lit parse` command. It will attempt to use LibreOffice or ImageMagick to automatically convert them to PDF before extraction.