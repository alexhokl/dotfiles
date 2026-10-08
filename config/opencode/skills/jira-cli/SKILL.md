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
- `jira-cli get comment` / `jira-cli list comments` / `jira-cli list projects` / `jira-cli list boards`
- `jira-cli list users` / `jira-cli list issue-transitions`
- Any read-only fetch or inspection command

If the user requests a mutating operation while in read-only mode, respond:
> "I am currently in plan/read-only mode. I can describe what this operation would do, but I will not execute it until plan mode ends."

## Prerequisites

1. The `jira-cli` binary must be compiled and available in the system's PATH. If not compiled, it can be built from source in the repository using `task install` or `go build -o jira-cli main.go`.
2. A configuration file must exist at `~/Library/Application Support/jira-cli/config.yaml` (the default of the `--config` flag) containing:
   ```yaml
   email: user@testing.com
   api_key: your_jira_api_key
   organization: your_org_name
   client_id: ...        # OAuth credentials (optional, used by some flows)
   client_secret: ...
   port: 8080
   ```
   The `organization` value is the Atlassian Cloud site subdomain (e.g. `your_org_name` → `https://your_org_name.atlassian.net`).

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

Issue descriptions containing `expand` or `nestedExpand` ADF blocks are rendered
as a bold title followed by two-space-indented content:

```
**Section Title**
  Content inside the expand block.
```

To list issues (supports robust filtering):
```bash
jira-cli list issues --project <KEY> --status "<status>" --assignee <me|unassigned> --type <Bug|Task> [--limit <n>]
jira-cli list issues --jql "<raw JQL query>"
# JSON output
jira-cli list issues --project <KEY> --format json
```

To list comments of an issue:

```bash
jira-cli list comments -i <issue-id>
# Without metadata headers (ID, author, date per comment)
jira-cli list comments -i <issue-id> --comment-only
# JSON output (body is raw ADF)
jira-cli list comments -i <issue-id> --format json
```

To get a single comment of an issue:

```bash
jira-cli get comment --id <issue-id> --comment-id <comment-id>
# Without metadata header (ID, author, date)
jira-cli get comment --id <issue-id> --comment-id <comment-id> --comment-only
# JSON output (body is raw ADF)
jira-cli get comment --id <issue-id> --comment-id <comment-id> --format json
```

To list sprints of a board:

```bash
jira-cli list boards --type scrum
jira-cli list sprints --state active --state future -b <board-id>
```
To list the earliest future sprints of a board:

```bash
jira-cli list boards --type scrum
jira-cli list sprints --state future -b <board-id> --limit 1
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

#### Using the `expand` component in descriptions and comments

To include a collapsible expand section, use the `:::expand` / `:::` fenced
syntax in any markdown input (description file, `--message`, or the `$EDITOR`
workflow):

```markdown
Normal paragraph before the expand.

:::expand Section Title
This content will be rendered inside the expand block in Jira.

- Bullet lists, headings, code blocks, and other block types are supported.
:::

Normal paragraph after the expand.
```

- The title is everything after `:::expand` on the opening line (may be empty).
- All standard markdown block types (headings, lists, code blocks, blockquotes,
  tables, inline formatting) are supported inside the body.
- The closing `:::` is required; if omitted, the body is captured until end of
  input.

### 3. Updating Resources
To update an existing issue or transition its status:
```bash
jira-cli update issue -i <issue-id>
```
*Optional flags:* `-t <transition-name>` (to change status), `--type <name|id>` (to change issue type), `-a <assignee|none>` (to assign/unassign), `-s "<new summary>"`, `--parent <key|none>` (to assign/remove parent), `--add-label <label>`, `--delete-label <label>`, `--link-issue <key>` + `--link-type <name>` (create an issue link), `--sprint <id|name>` (move to sprint; `none` for backlog), `--no-notify` (suppress notification emails).

*(Note: Use `jira-cli list issue-transitions` to see available transitions for `-t`)*

To link two issues (the link is created **outward** from the `-i` issue; e.g. this makes PROJ-456 show "is blocked by" PROJ-123):
```bash
jira-cli update issue -i PROJ-123 --link-issue PROJ-456 --link-type Blocks
```
*(Use `jira-cli list link-types` to see available type names and their inward/outward descriptions)*

#### ⚠️ Gotcha: `--parent none` is a silent no-op for sub-tasks

The CLI reports success ("Issue X updated") but Jira **ignores** `update.parent.set.none` for `Sub-task` type issues (it only detaches standard issue types). Sub-tasks also cannot exist without a parent.

**Working method to detach + convert a sub-task to a standalone issue** — use the Jira Cloud **Bulk move API** (`POST /rest/api/3/bulk/issues/move`), which is asynchronous (returns a `taskId`, poll `GET /rest/api/3/bulk/queue/<taskId>` until `COMPLETE`):
```bash
# Extract credentials (never echo them)
f="$HOME/Library/Application Support/jira-cli/config.yaml"
email=$(grep '^email:' "$f" | sed -E 's/^email:[[:space:]]*//' | tr -d '"'"'"'')
key=$(grep '^api_key:' "$f" | sed -E 's/^api_key:[[:space:]]*//' | tr -d '"'"'"'')

curl -sS -u "$email:$key" -X POST "https://<org>.atlassian.net/rest/api/3/bulk/issues/move" \
  -H "Content-Type: application/json" \
  -d '{"sendBulkNotification":false,"targetToSourcesMapping":{"GSC,3,":{"inferClassificationDefaults":true,"inferFieldDefaults":true,"inferStatusDefaults":true,"inferSubtaskTypeDefault":false,"issueIdsOrKeys":["GSC-123"]}}}'
```
Where the mapping key is `<targetProjectKey>,<targetIssueTypeId>,<optionalTargetParentKey>` (trailing comma required when no parent; e.g. `GSC,3,` = project GSC, type ID 3 = Task, no parent). The `infer*Defaults: true` flags preserve status/fields without manual mappings. Up to 1000 issues per request; moving sub-task → standard type in the same project removes the parent automatically and preserves status, assignee, sprint, etc.

Verify afterwards:
```bash
jira-cli list issues --jql "parent = <PARENT-KEY>"      # expect: No issues found
jira-cli get issue -i <child-key>                        # check type/status
```

*(The legacy `POST /rest/api/2/issue/<key>/movesubtasks` endpoint returns 404 on Cloud. Also note `jira-cli get issue` does not support `--format json`.)*

#### ⚠️ Gotcha: `--sprint "name"` may fail to resolve

The CLI resolves sprint names only via boards it can list for the project; sprints on other boards won't be found. **Workaround: use the sprint ID directly** (`--sprint 2322`). To find a sprint's ID when other issues already have it, query the Sprint field (`customfield_10007`) via the REST API:
```bash
curl -sS -u "$email:$key" -G "https://<org>.atlassian.net/rest/api/3/search/jql" \
  --data-urlencode 'jql="Sprint" = "<sprint name>"' \
  --data-urlencode "fields=customfield_10007" --data-urlencode "maxResults=1"
```
The sprint object in the response contains `id`, `boardId`, and `state`. (Note: `/rest/api/3/search` was removed — use `/rest/api/3/search/jql` with `--data-urlencode` for JQL.)

### 4. Other Available Entities

The CLI also supports full CRUD and list operations for other Jira entities. Discover flags using `--help` if needed:
- `jira-cli [list|get|create|update|start|close] sprint`
- `jira-cli [list|get|create|update|delete] status`
- `jira-cli list projects`, `list boards`, `list users`, `list labels`, `list workflows`, `list custom-fields`, `list sprints`
- `jira-cli list issue-transitions`, `list issue-types`, `list issue-type-schemes`, `list workflow-schemes`, `list workflow-status`, `list workflow-status-properties`, `list link-types`, `list custom-field-values`
- `jira-cli bulk-update custom-field-value`, `rename-label`, `delete-label`

Most `list` subcommands accept both singular and plural subject names
(e.g. `list issue` and `list issues` are equivalent). They also accept:
- `--limit <n>` to cap the number of results returned (default `0` = all)
- `--format json` to emit JSON instead of the default table output

**Notes on `--format json`:**
- `list comments`: the `body` field contains the raw Atlassian Document Format (ADF) JSON tree.
- `list issues`: `--id-only` and `--format json` are mutually exclusive.
- `list custom-field-values`: `--id-only` / `--value-only` take precedence over `--format json`.

## Direct REST API fallback

When the CLI lacks an operation (e.g. bulk move, sub-task conversion), call the Jira Cloud REST API directly with Basic Auth (email + API key) against `https://<organization>.atlassian.net/rest/api/3/...`. Extract credentials from the config file (see the bulk-move example above) and never print them. Useful endpoints:
- `POST /rest/api/3/bulk/issues/move` — bulk move / sub-task conversion (async)
- `GET /rest/api/3/bulk/queue/<taskId>` — poll async task status
- `GET /rest/api/3/myself` — quick auth check
