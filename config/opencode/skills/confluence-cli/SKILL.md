---
name: confluence-cli
description: Use when the user asks to manage, read, create, update, or list Confluence pages and spaces directly from the terminal.
---

# confluence-cli Skill

This skill provides `opencode` with the ability to interact with Atlassian Confluence Cloud via the local `confluence-cli` application.

## Plan / Ask Mode (Read-Only)

Before executing any command, check whether a `<system-reminder>` block containing `Plan mode ACTIVE` is present in your current context. If it is, you are in **read-only mode** and MUST NOT execute any command that creates, updates, or deletes data.

**Forbidden in read-only mode:**
- `confluence-cli create page`
- `confluence-cli update page`
- `confluence-cli delete page` / `confluence-cli delete space`
- Any command that writes or modifies content in Confluence

**Allowed in read-only mode:**
- `confluence-cli get page` / `confluence-cli list pages`
- `confluence-cli list spaces` / `confluence-cli search`
- Any read-only fetch or inspection command

If the user requests a mutating operation while in read-only mode, respond:
> "I am currently in plan/read-only mode. I can describe what this operation would do, but I will not execute it until plan mode ends."

## Prerequisites
1. The `confluence-cli` binary must be compiled and available in the system's `PATH`. If not compiled, it can be built from source in the repository using `task install` or `go build -o confluence-cli .`.
2. A configuration file must exist at `~/.config/confluence-cli/config.yaml` containing:
   ```yaml
   email: user@domain.com
   api_key: your_confluence_api_token
   organization: your_confluence_domain
   ```
   *(Note: The organization is the subdomain of your Atlassian URL, e.g., for `https://my-org.atlassian.net`, use `my-org`). Alternatively, configuration can be provided via environment variables (`CONFLUENCE_CLI_EMAIL`, `CONFLUENCE_CLI_API_KEY`, `CONFLUENCE_CLI_ORGANIZATION`).*

## How to use this skill
When the user asks to manage or fetch Confluence items, follow these steps:
1. Verify `confluence-cli` is accessible by running `confluence-cli --help`.
2. Formulate the appropriate command based on the user's intent using the examples below.
3. Execute the command using the `bash` tool.

## Key Commands & Workflows

### 1. Fetching Information
To get a single page's content:
```bash
confluence-cli get page -i <page-id> [--format <storage|atlas_doc_format|view|md>] [--no-images] [--view]
```

To list pages (supports filtering by space, status, and title):
```bash
confluence-cli list pages --space-key <KEY> --status <current|archived|trashed> --title "<partial title>"
```

To list spaces:
```bash
confluence-cli list spaces --limit <limit> --type <global|personal> --status <current|archived>
```

To get the page tree of a space:
```bash
confluence-cli get tree --space-key <KEY> [--title "<partial title>"] [--parent-id <page-id>]
```

### 2. Creating Resources
To create a new page, use the `create page` command. 
**Note:** This command only creates an *empty* published page. To add content, you must immediately follow up with an `update page` command (see below).
```bash
confluence-cli create page -t "<page title>" --space-key <KEY>
```
*Optional flags:* `--space-id <id>`, `--parent-id <id>` (to create as a child page).

### 3. Updating Resources (IMPORTANT NON-INTERACTIVE WORKFLOW)
The `update page` command works by converting Confluence storage format to Markdown, opening it in a text editor (via the `$EDITOR` environment variable), and converting it back upon save. 

Because `opencode` is non-interactive, **you cannot use interactive editors like `vim` or `nano`**. Instead, you must mock the `$EDITOR` using a bash script that overwrites the provided file path with your new Markdown content.

**Example Agent Workflow for Updating a Page:**
```bash
# 1. Write the new markdown content to a file
cat << 'EOF' > new_content.md
# Updated Page Title
Here is the new content formatted in **Markdown**.
EOF

# 2. Create a mock editor script that dumps the new content into the file path passed by the CLI
cat << 'EOF' > mock_editor.sh
#!/bin/bash
cat new_content.md > "$1"
EOF
chmod +x mock_editor.sh

# 3. Run the update command using the mock editor
EDITOR=./mock_editor.sh confluence-cli update page --id <page-id> -m "Updated via opencode"
```

### 4. Deleting Resources
To permanently delete a space (requires admin privileges for the space):
```bash
confluence-cli delete space -k <space-key>
```
