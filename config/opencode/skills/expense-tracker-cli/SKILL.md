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

**All dates use the format `YYYY-MM-DD`; budget months use `YYYY-MM`.**

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
| `list budget` (`budgets`)     | `-t/--expense-type`, `-m/--month` (covering this `YYYY-MM`), `--format text\|json`, `--fields` (`id,expense_type,currency,start_month,end_month,allocations,total`)                          |
| `list income-budget`          | `-t/--income-type`, `-m/--month`, `--format text\|json`, `--fields` (`id,income_type,currency,start_month,end_month,allocations,total`)                                                       |

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
| `get report budget`              | `--start` `YYYY-MM` (default this month), `-e/--end` `YYYY-MM` (default this month); inherits `--format text\|json\|csv` and `-c/--currency` (default: the default currency). Outputs a monthly matrix of budget allocations per expense type converted to the report currency, sorted by total descending, with a `%` column and `Total` footer row. Fails listing every missing exchange rate. |
| `get report income-budget`       | Same as `get report budget`, for income budgets.                                                                    |
| `get report asset-forecast`      | `--start`, `-e/--end` (`YYYY-MM-DD`), `--display-currency` (default: the default currency). Cashflow forecast: income and expense budget allocations and running asset balance per month. |
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
| `create budget`              | `-t/--expense-type`*, `-c/--currency`*, `--start`* `YYYY-MM`, `--end`* `YYYY-MM`, and exactly one of `-a/--amount` (every month), `--total` (split evenly), `--allocations` (`YYYY-MM=amount,...` covering every month) |
| `create income-budget`       | Same as `create budget` with `-t/--income-type`*                                                                                                                                      |
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
| `update budget` / `update income-budget` | `--id`*, then at least one of: `-c/--currency`, `--start`, `--end` (`YYYY-MM`), `--allocations` (`YYYY-MM=amount,...`; required for months added to the range) |
| `update budget-allocation` / `update income-budget-allocation` | `--id`*, `--month`* `YYYY-MM`, `-a/--amount`* (zero allowed) |

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
| `delete income-budget` | `--id`*                        |

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

Manage budgets (a budget holds one allocation per calendar month):

```bash
# The same amount every month of 2027
go-ali-expense-tracker create budget \
  --expense-type food --currency hkd --start 2027-01 --end 2027-12 --amount 3000

# A yearly total split evenly (remainder goes to the last month)
go-ali-expense-tracker create budget \
  --expense-type travel --currency hkd --start 2027-01 --end 2027-12 --total 30000

# Different amounts per month (zero allowed)
go-ali-expense-tracker create budget \
  --expense-type school --currency hkd --start 2027-07 --end 2027-09 \
  --allocations "2027-07=8000,2027-08=0,2027-09=8000"

# Change one month
go-ali-expense-tracker update budget-allocation --id 3 --month 2027-03 --amount 600

# Extend a budget; new months must be given
go-ali-expense-tracker update budget --id 3 --end 2028-02 \
  --allocations "2028-01=3000,2028-02=3000"

# List budgets covering a month
go-ali-expense-tracker list budgets --month 2027-02 --format json

# Delete a budget by ID
go-ali-expense-tracker delete budget --id 3
```

Budget report (monthly matrix of budget allocations):

```bash
# Text output for H1 2027 in the default currency
go-ali-expense-tracker get report budget --start 2027-01 --end 2027-06

# CSV output in USD
go-ali-expense-tracker get report budget --start 2027-01 --end 2027-06 --currency usd --format csv
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
- Amounts must be greater than zero (budget allocations may be zero).
- `create budget`: `--start` has no `-s` shorthand; `-s` is reserved for the
  global `--service` flag. Use `--start` (long form only).
- `create budget` / `update budget`: the server rejects a month range that
  overlaps another budget for the same type; at most one allocation exists per
  type per month. At least one allocation must be positive.
- Budget reports, the expense report and the asset forecast fail with a list of
  every missing exchange rate when a budget currency differs from the report
  currency; create those rates with `create exchange_rate` first. Rates are
  looked up on the first day of each month.
- `get report expense`: budgets are only shown for `--period month` and `year`.
- `get report expense`: `--expense-type` is optional. When omitted, output is a
  matrix of all expense types. When specified, output shows per-period rows for
  that type with budget comparison and statistics.
- When unsure of exact flags, run `go-ali-expense-tracker <command> --help`.
