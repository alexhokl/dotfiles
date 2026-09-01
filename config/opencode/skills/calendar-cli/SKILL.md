---
name: calendar-cli
description: Use when the user asks to list, create, delete, move, or manage Google Calendar calendars and events directly from the terminal. Covers listing calendars and events, creating single or bulk events (including from JSON files or stdin), bulk-deleting events by search, and moving (fitting) events to a different week.
---

# calendar-cli Skill

This skill provides `opencode` with the ability to interact with Google Calendar via the local `calendar-cli` application (a Go/Cobra CLI).

## Plan / Ask Mode (Read-Only)

Before executing any command, check whether a `<system-reminder>` block containing `Plan mode ACTIVE` is present in your current context. If it is, you are in **read-only mode** and MUST NOT execute any command that creates, updates, or deletes data.

**Forbidden in read-only mode:**
- `calendar-cli create event` / `calendar-cli create events`
- `calendar-cli delete events`
- `calendar-cli fit-calendar-to-week`
- `calendar-cli login` (writes OAuth tokens to config)

**Allowed in read-only mode:**
- `calendar-cli list calendars`
- `calendar-cli list events`
- Any read-only fetch or inspection command

If the user requests a mutating operation while in read-only mode, respond:
> "I am currently in plan/read-only mode. I can describe what this operation would do, but I will not execute it until plan mode ends."

## ⚠️ Destructive command warning

`delete events` **bulk-deletes every event matching the given filters with no confirmation prompt and no `--dry-run` option**. Before deleting:

1. Run `list events` with the exact same filters (`-c`, `--search`, `--start`, `--end`) to preview what will be removed.
2. Confirm the result with the user.
3. Only then run `delete events`.

`fit-calendar-to-week` is also destructive: it moves (patches) the dates of **all matched events** to the target week.

## Prerequisites

1. The `calendar-cli` binary must be available in PATH. If not, build and install from the repository:
   ```bash
   cd ~/git/calendar-cli && go install
   # or: task install
   ```
2. One-time OAuth setup (requires credentials from Google Cloud Console):
   ```bash
   calendar-cli login --client-id <client-id> --client-secret <client-secret>
   # or: calendar-cli login --credentials /path/to/credentials.json
   ```
3. Configuration and tokens are stored in:
   - macOS: `~/Library/Application Support/calendar-cli/config.yaml`
   - Linux: `$XDG_CONFIG_HOME/calendar-cli/config.yaml`
   - Override with the global `--config <path>` flag.

## Critical usage rules for agents

- **Always pass `--non-interactive` for scripted/agent use.** Without it, `list` and `delete` commands open interactive prompts (calendar selection, date-range picker) that will hang a non-interactive session. When using `--non-interactive`, you must also explicitly pass `-c/--calendar`, `--start`, and `--end`.
- **All dates and times are RFC3339 with timezone offset**, e.g. `2026-09-07T09:00:00+08:00`.
- **`-c/--calendar` takes a calendar ID**, not a display name. Discover IDs with `calendar-cli list calendars -q`. The `create` commands default to `primary`.
- Durations use Go duration syntax: `90m`, `1h30m`, `45m`.
- When unsure of exact flags, run `calendar-cli <command> --help`.

## Command reference

### `login` — OAuth login

| Flag | Purpose |
| ---- | ------- |
| `--credentials <file>` | Path to credentials JSON downloaded from Google Cloud Console |
| `--client-id <id>` | OAuth Client ID (alternative to credentials file) |
| `--client-secret <secret>` | OAuth Client Secret (alternative to credentials file) |

Client ID/secret are remembered after the first login; subsequent logins can omit them.

### `list calendars` (aliases: `calendar`, `c`)

| Flag | Purpose |
| ---- | ------- |
| `-q, --quiet` | Only print calendar IDs |
| `--search <text>` | Filter calendars by summary text |
| `--non-interactive` | Non-interactive table output |

Note: only calendars where the user is an **owner** are listed (other calendars are filtered out).

### `list events` (aliases: `event`, `e`)

| Flag | Purpose |
| ---- | ------- |
| `-n, --limit <n>` | Maximum number of events (default 10; forced to 2500 in interactive mode) |
| `-c, --calendar <id>` | Calendar ID (prompts interactively if omitted and not `--non-interactive`) |
| `--search <text>` | Search query for events |
| `--start <rfc3339>` | Start of date range (required with `--non-interactive`) |
| `--end <rfc3339>` | End of date range (required with `--non-interactive`) |
| `-q, --quiet` | Only display event IDs |
| `--non-interactive` | Disable interactive prompts |

### `create event` (alias: `e`)

| Flag | Purpose |
| ---- | ------- |
| `-s, --start <rfc3339>` * | Start date and time |
| `--summary <text>` * | Title of the event |
| `-d, --duration <dur>` | Duration (default `1h`) |
| `--description <text>` | Description of the event |
| `-c, --calendar <id>` | Calendar ID (default `primary`) |

### `create events` — bulk create from JSON

| Flag | Purpose |
| ---- | ------- |
| `-f, --file <path>` * | JSON file path, or `-` for stdin |
| `-c, --calendar <id>` | Calendar ID (default `primary`) |

JSON schema — an array of objects:

```json
[
  {
    "summary": "Event title",
    "description": "Optional description",
    "start": "2026-09-07T09:00:00+08:00",
    "duration": "1h30m"
  }
]
```

- `start` is RFC3339 and parses as a `time.Time` — it must be a full RFC3339 timestamp.
- **If `duration` is empty or omitted, the event is created as an all-day event** on the date of `start`.

### `delete events` (aliases: `event`, `e`) — destructive

| Flag | Purpose |
| ---- | ------- |
| `-c, --calendar <id>` | Calendar ID (prompts interactively if omitted and not `--non-interactive`) |
| `--search <text>` | Search query for events |
| `--start <rfc3339>` | Start of date range (required with `--non-interactive`) |
| `--end <rfc3339>` | End of date range (required with `--non-interactive`) |
| `--non-interactive` | Disable interactive prompts |

Deletes **all** events matching the filters. Always preview with `list events` first (see the destructive command warning above).

### `fit-calendar-to-week` — move events to a target week

Moves all events of the specified calendar to another week while **respecting the original day of week and time of day**. Scans events from last year through end of next year.

| Flag | Purpose |
| ---- | ------- |
| `-d, --date <rfc3339>` | A date within the target week (XOR with `--week`) |
| `-w, --week <1-53>` | ISO week number of the target week (XOR with `--date`) |
| `-c, --calendar <id>` | Calendar ID (default `primary`) |
| `--search <text>` | Only move events matching the query |

Exactly one of `--date` or `--week` must be specified, not both.

### `completion <shell>`

Generates autocompletion scripts for `bash`, `zsh`, `fish`, or `powershell`:

```bash
# macOS (homebrew bash-completion)
calendar-cli completion bash > /opt/homebrew/etc/bash_completion.d/calendar-cli

# Linux
calendar-cli completion bash | sudo tee /etc/bash_completion.d/calendar-cli
```

## Common workflows

### Discover calendar IDs

```bash
calendar-cli list calendars -q
```

### Search events in a date window (non-interactive)

```bash
calendar-cli list events \
  --non-interactive \
  -c <calendar-id> \
  --search "standup" \
  --start 2026-09-01T00:00:00+08:00 \
  --end 2026-09-30T23:59:59+08:00
```

### Create a single event

```bash
calendar-cli create event \
  -c <calendar-id> \
  -s 2026-09-07T09:00:00+08:00 \
  -d 1h30m \
  --summary "Team sync" \
  --description "Weekly sync meeting"
```

### Bulk create events from a JSON file

```bash
cat > events.json <<'EOF'
[
  {"summary": "Deep work", "start": "2026-09-07T09:00:00+08:00", "duration": "2h"},
  {"summary": "Company holiday", "start": "2026-10-01T00:00:00+08:00"}
]
EOF
calendar-cli create events -c <calendar-id> -f events.json
```

Or stream from stdin:

```bash
cat events.json | calendar-cli create events -c <calendar-id> -f -
```

### Bulk create from Airtable records

```bash
curl -s "https://api.airtable.com/v0/${AIRTABLE_TODO_WEEK_BASE_ID}/Week?maxRecords=100&view=${AIRTABLE_TODO_WEEK_VIEW_NAME}" \
  -H "Authorization: Bearer ${AIRTABLE_PERSONAL_ACCESS_TOKEN}" | \
  jq '[.records[] | { summary: ( .fields.Category + " - " + .fields.Name), start:.fields.Start, duration: ((.fields.Hours|tostring) + "h"), description: .fields.Notes }]' |\
  calendar-cli create events -c ${CALENDAR_ID} -f -
```

### Safe delete pattern

Always preview before deleting:

```bash
# 1. Preview what matches
calendar-cli list events \
  --non-interactive \
  -c <calendar-id> \
  --search "old meeting" \
  --start 2026-01-01T00:00:00+08:00 \
  --end 2026-06-30T23:59:59+08:00

# 2. Confirm with the user, then delete with the SAME filters
calendar-cli delete events \
  --non-interactive \
  -c <calendar-id> \
  --search "old meeting" \
  --start 2026-01-01T00:00:00+08:00 \
  --end 2026-06-30T23:59:59+08:00
```

### Move a calendar's events to a specific week

```bash
# By date within the target week
calendar-cli fit-calendar-to-week -c <calendar-id> -d 2026-09-07T00:00:00+08:00

# By ISO week number
calendar-cli fit-calendar-to-week -c <calendar-id> -w 37
```

## Gotchas

- Interactive prompts (calendar picker, date-range picker) hang scripted runs — always use `--non-interactive` with explicit `-c`, `--start`, `--end`.
- `delete events` has no confirmation or dry-run; preview with `list events` using identical filters first.
- `--start`/`--end` are **both required** when using `--non-interactive` on `list events` / `delete events`.
- `list events --limit` defaults to 10; raise it (e.g. `-n 100`) when searching.
- `fit-calendar-to-week` requires exactly one of `-d/--date` or `-w/--week` (never both).
- `fit-calendar-to-week` moves all matched events from a window spanning last year to end of next year — scope with `--search` to limit blast radius.
- Empty `duration` in bulk-created events means an all-day event.
- `list calendars` only shows calendars where the user is an owner.
