---
name: jira-cli
description: Use when the user asks to fetch, list, create, update, or manage Jira issues, sprints, boards, projects, and comments directly from the terminal.
---

# jira-cli Skill

This skill provides `opencode` with the ability to interact with Jira Cloud via the local `jira-cli` application.

## Plan / Ask Mode (Read-Only)

Before executing any command, check whether a `<system-reminder>` block containing `Plan mode ACTIVE` is present in your current context. If it is, you are in **read-only mode** and MUST NOT execute any command that creates, updates, transitions, or deletes data.

**Forbidden in read-only mode:**
- `jira-cli create issue` / `jira-cli create comment`
- `jira-cli update issue` (including status transitions via `-t`)
- `jira-cli bulk-update` / `jira-cli rename-label` / `jira-cli delete-label`
- `jira-cli [create|update|start|close] sprint`
- `jira-cli [create|update|delete] status`

**Allowed in read-only mode:**
- `jira-cli get issue` / `jira-cli list issues`
- `jira-cli list comments` / `jira-cli list projects` / `jira-cli list boards`
- `jira-cli list users` / `jira-cli list issue-transitions`
- Any read-only fetch or inspection command

If the user requests a mutating operation while in read-only mode, respond:
> "I am currently in plan/read-only mode. I can describe what this operation would do, but I will not execute it until plan mode ends."

## Prerequisites
1. The `jira-cli` binary must be compiled and available in the system's PATH. If not compiled, it can be built from source in the repository using `task install` or `go build -o jira-cli main.go`.
2. A configuration file must exist at `~/.jira-cli.yml` containing:
   ```yaml
   email: user@testing.com
   api_key: your_jira_api_key
   organization: your_org_name
   ```

## How to use this skill
When the user asks to manage or fetch Jira items, follow these steps:
1. Verify `jira-cli` is accessible by running `jira-cli --help`.
2. Formulate the appropriate command based on the user's intent using the provided flags below.
3. Execute the command using the `bash` tool.

## Key Commands & Workflows

### 1. Fetching Information
To get a single issue's details:
```bash
jira-cli get issue -i <issue-id> [--description-only] [--no-images]
```

To list issues (supports robust filtering):
```bash
jira-cli list issues --project <KEY> --status "<status>" --assignee <me|unassigned> --type <Bug|Task>
jira-cli list issues --jql "<raw JQL query>"
```

To list comments of an issue:

```bash
jira-cli list comments -i <issue-id>
```

### 2. Creating Resources
To create a new issue:
```bash
jira-cli create issue -p <project-key> -t <type> -s "<summary>"
```
*Optional flags:* `-d <desc-file.md>`, `-a <assignee>`, `--priority <priority>`, `-l <labels>`.

To add a comment to an issue:
```bash
jira-cli create comment -i <issue-id> -m "<comment body>"
```

### 3. Updating Resources
To update an existing issue or transition its status:
```bash
jira-cli update issue -i <issue-id>
```
*Optional flags:* `-t <transition-name>` (to change status), `-a <assignee|none>` (to assign/unassign), `-s "<new summary>"`, `--add-label <label>`, `--delete-label <label>`.

*(Note: Use `jira-cli list issue-transitions` to see available transitions for `-t`)*

### 4. Other Available Entities
The CLI also supports full CRUD and list operations for other Jira entities. Discover flags using `--help` if needed:
- `jira-cli [list|get|create|update|start|close] sprint`
- `jira-cli [list|get|create|update|delete] status`
- `jira-cli list projects`, `list boards`, `list users`
- `jira-cli bulk-update custom-field-value`, `rename-label`, `delete-label`
