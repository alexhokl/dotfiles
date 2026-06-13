---
name: expense-tracker-cli
description: Use when managing expense data (entries, expense/payment types, schedules, currencies, exchange rates, tax rates, reports, budgets) via the go-ali-expense-tracker CLI against a running server. Covers creating, listing, updating, deleting, copying entries and importing from CSV.
---

# expense-tracker-cli

`go-ali-expense-tracker` is a Go (Cobra) command-line client for the expense
tracker. It talks to a running gRPC/REST server. This skill explains how to
drive the CLI to manage data. It does **not** cover starting the server (the
`serve` subcommand is intentionally out of scope).

## ⚠️ Mode safety: mutating vs read-only commands

Commands under `create`, `update`, `delete`, and `copy` **mutate data**.

- Run mutating commands **only** in an action / edit-capable mode
  (opencode **Build / Agent** mode, or the equivalent in your tool).
- **Never** run mutating commands while in a read-only planning mode. This mode
  is called **"Plan mode"** in opencode and **"Ask mode"** in Zed and
  VS Code / GitHub Copilot (and similar names elsewhere).
- While in a planning / ask mode, restrict yourself to the read-only `list` and
  `get` commands, which never change data and are safe in any mode.

In opencode this is also enforced: Plan Mode denies `create`/`update`/`delete`/
`copy` invocations at the permission layer. Other tools rely on this guidance.

## Connecting to the server

Set the service URI once via an environment variable (read through viper with
the `tracker` prefix) so you don't have to pass `--service` on every call:

```bash
export TRACKER_SERVICE=localhost:8080      # host:port of the running server
```

Other environment variables:

| Variable           | Flag equivalent   | Purpose                                  |
| ------------------ | ----------------- | ---------------------------------------- |
| `TRACKER_SERVICE`  | `-s, --service`   | Service URI (required, one way or other) |
| `TRACKER_INSECURE` | `-i, --insecure`  | Allow insecure connection                |
| `TRACKER_CONFIG`   | `--config`        | Path to config file                      |

TLS is auto-detected: connections to `localhost`, `127.0.0.1`, or `[::1]` use
plaintext; any other host uses system-certificate TLS.

**All dates use the format `YYYY-MM-DD`.**

If `TRACKER_SERVICE` is not set, pass `-s host:port` explicitly. Confirm any
command's flags with `go-ali-expense-tracker <command> --help`.

## Read-only commands (safe in any mode)

### `list` — list records

All `list` subcommands support `--format text|json` and `--fields` (a
comma-separated subset of fields to include in JSON output). Each subcommand has
a plural alias (e.g. `entries`).

| Command                       | Notable flags                                                                                                                                                                                 |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `list entry` (`entries`)      | `-d/--date`, `--limit` (default 10), `--no-limit`, `-e/--expense`, `-p/--payment`, `-c/--currency`, `-y/--year`, `-m/--month`, `-w/--week`, `--scheduled`, `--display-currency`, `--format`, `--fields` |
| `list income` (`incomes`)     | `-d/--date`, `--limit` (default 10), `--no-limit`, `-t/--income-type`, `-c/--currency`, `-y/--year`, `-m/--month`, `--display-currency`, `--format`, `--fields`                                |
| `list asset-balance`          | `--asset-id`* (required), `-d/--date`, `-y/--year`, `-m/--month`, `--display-currency`, `--limit` (default 10), `--no-limit`, `--format`, `--fields`                                           |
| `list expense` (`expenses`)   | `--format`, `--fields` (`name`)                                                                                                                                                                |
| `list payment` (`payments`)   | `--format`, `--fields` (`name`)                                                                                                                                                                |
| `list schedule` (`schedules`) | `--format`, `--fields` (`id,start,end,frequency,description,payment_type,expense_type,amount`)                                                                                                 |
| `list exchange_rate`          | `-c/--currency` (multi), `-d/--date`, `--format`, `--fields` (`id,from,to,rate,valid_from,valid_to`)                                                                                           |
| `list tax_rate` (`tax_rates`) | `-c/--currency` (multi), `-n/--name`, `-d/--date`, `--format`, `--fields` (`id,name,currency,rate,valid_from,valid_to`)                                                                        |
| `list budget` (`budgets`)     | `-t/--expense-type`, `-d/--date` (active on this date), `--format text\|json`, `--fields` (`id,expense_type,amount,currency,start_date,end_date`)                                              |

`list entry` JSON fields: `id,date,description,payment_type,expense_type,amount,currency,scheduled`.

### `get` — retrieve values, reports, and templates

| Command                          | Notable flags                                                                                                       |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `get entry`                      | `--id`* (required), `--format text\|json`, `--fields` (`id,date,description,payment_type,expense_type,amount,currency,scheduled`) |
| `get currency`                   | (none) Prints the default currency.                                                                                 |
| `get report monthly`             | `-y/--year`, `-m/--month`                                                                                            |
| `get report weekly`              | `-y/--year`, `-w/--week`                                                                                             |
| `get report daily`               | `-y/--year`, `-m/--month`, `-d/--day`                                                                                |
| `get report expense`             | `--start`, `-e/--end`, `-p/--period day\|week\|month\|year` (default `month`), `-t/--expense-type` (optional; omit to show all expense types as a matrix); inherits `--format text\|json\|csv` and `-c/--currency`; output includes `Budget` and `Diff` columns alongside `Sum` |
| `get report budget`              | `--start` (default today), `-e/--end` (default today); inherits `--format text\|json\|csv`. Outputs a monthly matrix of budget amounts per expense type, sorted by total descending, with a `%` column and `Total` footer row. |
| `get bulk_create_csv_template`   | Writes a CSV header + example row to stdout (for `create entries_from_csv`).                                         |

`get report` shares persistent flags: `--format text|json|csv`, `-c/--currency`,
`--groupby expense|payment`, `--exclude` (comma-separated categories to drop).
Report flags default year/month/week/day to the current date.
`get report expense` returns per-period sums (week or month labels) plus
cross-period statistics (average, median, population standard deviation) for a
single expense type over an arbitrary date range.

## Mutating commands (action / edit mode only)

Required flags are marked `*`.

### `create`

| Command                      | Flags                                                                                                                                                                                |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `create entry`               | `-a/--amount`*, `-d/--date`*, `-e/--expense`* (multi), `-p/--payment`*, `--description`, `-c/--currency`, `--tax-rate-id`                                                              |
| `create entries_from_csv`    | `-f/--file`* (path, or `-` for stdin). CSV columns: `date,amount,currency,description,expense_types,payment_type` (currency optional; `expense_types` comma-separated). Atomic import. |
| `create scheduled_entries`   | `--start`*, `--end`*, and **either** `--id` (multi) **or** `--name` (multi), not both                                                                                                 |
| `create schedule`            | `-a/--amount`*, `-e/--expense`* (multi), `-p/--payment`*, `-f/--frequency`*, `--start`, `--end`, `--description`, `-c/--currency` (default HKD)                                        |
| `create expense`             | `-n/--name`*                                                                                                                                                                          |
| `create payment`             | `-n/--name`*                                                                                                                                                                          |
| `create exchange_rate`       | `--base`*, `--target`*, `-r/--rate`*, `--from`*, `--to`*                                                                                                                              |
| `create tax_rate`            | `-n/--name`*, `-c/--currency`*, `-r/--rate`* (percent, must be < 100), `--from`*, `--to`*                                                                                             |
| `create budget`              | `-t/--expense-type`*, `-a/--amount`*, `-c/--currency`*, `--start`*, `--end`* (no `-s` shorthand on `--start`; `-s` is reserved for the global `--service` flag)                       |
| `create income`              | `-a/--amount`*, `-d/--date`*, `-t/--income-type`* (multi), `-c/--currency`*, `--description`, `--expense-type` (expense type this income offsets, e.g. a refund)                      |

Valid `--frequency` values: `daily`, `weekly`, `biweekly`, `monthly`,
`quarterly`, `yearly`, `weekdays`, `weekends`, `saturday`, `sunday`.

### `update`

| Command           | Flags                                                                                                                                                                            |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `update entry`    | `--id`* (multi), then at least one of: `--description`, `-a/--amount`, `-c/--currency`, `-d/--date`, `--add-expense` (multi), `--remove-expense` (multi), `-p/--payment`, `--tax-rate-id` |
| `update income`   | `--id`* (multi), then at least one of: `--description`, `-a/--amount`, `-c/--currency`, `-d/--date`, `--add-income-type` (multi), `--remove-income-type` (multi), `--expense-type`, `--no-expense-type` (clear expense type; mutually exclusive with `--expense-type`) |
| `update schedule` | `--id`*, then at least one of: `--name`, `--description`, `-a/--amount`, `-c/--currency`, `--start-date`, `--end-date`, `-f/--frequency`, `--add-expense`, `--remove-expense`, `-p/--payment` |
| `update currency` | `-c/--code`*                                                                                                                                                                    |

### `delete`

| Command                | Flags                          |
| ---------------------- | ------------------------------ |
| `delete entry`         | `--id`*                        |
| `delete expense`       | `--id`* (see `--help`)         |
| `delete payment`       | `--id`* (see `--help`)         |
| `delete schedule`      | `--id`* (see `--help`)         |
| `delete exchange_rate` | `--id`* (see `--help`)         |
| `delete tax_rate`      | `-i/--id`*                     |
| `delete budget`        | `-i/--id`*                     |

### `copy`

| Command         | Flags                                       |
| --------------- | ------------------------------------------- |
| `copy entries`  | `-d/--date`* (target date), `--id`* (multi) |

## Common workflows

Assume `TRACKER_SERVICE` is exported.

Create an entry:

```bash
go-ali-expense-tracker create entry \
  -a 25.50 -d 2026-01-15 -e food -e groceries -p "credit card" \
  --description "Grocery shopping" -c USD
```

List this month's entries as JSON with selected fields:

```bash
go-ali-expense-tracker list entries -y 2026 -m 1 \
  --format json --fields id,date,description,amount,currency
```

Bulk import from CSV:

```bash
go-ali-expense-tracker get bulk_create_csv_template > entries.csv
# edit entries.csv
go-ali-expense-tracker create entries_from_csv -f entries.csv
# or stream: cat entries.csv | go-ali-expense-tracker create entries_from_csv -f -
```

Monthly report as CSV grouped by payment type:

```bash
go-ali-expense-tracker get report monthly -y 2026 -m 1 \
  --groupby payment --format csv
```

Generate entries from schedules over a date range:

```bash
go-ali-expense-tracker create scheduled_entries --start 2026-01-01 --end 2026-01-31
```

Expense trend report for a single expense type over a date range:

```bash
# Weekly sums + statistics for "food" over Q1 2026, output as CSV
go-ali-expense-tracker get report expense \
  --expense-type food --start 2026-01-01 --end 2026-03-31 \
  --period week --format csv

# Monthly, JSON output
go-ali-expense-tracker get report expense \
  --expense-type transport --start 2026-01-01 --end 2026-12-31 \
  --period month --format json --currency usd
```

Manage budgets:

```bash
# Create a food budget for Q1 2026
go-ali-expense-tracker create budget \
  --expense-type food --amount 3000 --currency hkd \
  --start 2026-01-01 --end 2026-03-31

# List all budgets active on a specific date
go-ali-expense-tracker list budgets --date 2026-02-15

# List all food budgets as JSON
go-ali-expense-tracker list budgets --expense-type food --format json

# Delete a budget by ID
go-ali-expense-tracker delete budget --id 3
```

Budget report (monthly matrix of actuals vs budgets):

```bash
# Text output for H1 2026
go-ali-expense-tracker get report budget --start 2026-01-01 --end 2026-06-30

# CSV output
go-ali-expense-tracker get report budget --start 2026-01-01 --end 2026-06-30 --format csv
```

Get a single entry by ID:

```bash
go-ali-expense-tracker get entry --id 42
go-ali-expense-tracker get entry --id 42 --format json --fields id,date,amount,currency
```

## Gotchas

- Prefer `--format json` (plus `--fields`) when you need to parse output.
- `list entry`: `--year` is required when `--month` or `--week` is given;
  `--month` and `--week` cannot be combined.
- `list entry` / `list income` / `list asset-balance`: `--limit` and `--no-limit`
  are mutually exclusive.
- `create scheduled_entries`: use `--id` **or** `--name`, never both.
- `update entry` / `update schedule` / `update income`: at least one field flag
  must be supplied in addition to `--id`.
- `update income`: `--expense-type` and `--no-expense-type` are mutually exclusive.
- `create tax_rate`: `--rate` is a percent and must be `> 0` and `< 100`.
- Amounts must be greater than zero.
- `create budget`: `--start` has no `-s` shorthand; `-s` is reserved for the
  global `--service` flag. Use `--start` (long form only).
- `create budget` / `list budget`: the server rejects a new budget whose date
  range overlaps an existing budget for the same expense type. Adjacent ranges
  (one ends the day before the other starts) are allowed.
- `get report expense`: `--expense-type` is optional. When omitted, output is a
  matrix of all expense types. When specified, output shows per-period rows for
  that type with budget comparison and statistics.
- When unsure of exact flags, run `go-ali-expense-tracker <command> --help`.
