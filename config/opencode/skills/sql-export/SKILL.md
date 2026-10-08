---
name: sql-export
description: Use when the user wants to run sql-export, dump SQL data from MSSQL or PostgreSQL to screen or Google Sheets, author or edit sql-export config files, or troubleshoot sql-export errors. Trigger keywords including 'sql-export', 'dump SQL data', 'Google Sheets export', 'export query results', 'sql-export config'.
---

# SQL export CLI

Exports SQL query results from MSSQL or PostgreSQL to screen or a new Google Sheets document.

## Install / locate binary

```bash
which sql-export || go install github.com/alexhokl/sql-export@latest
```

## Commands

```bash
sql-export screen  -c config.yml [-r key:value ...]   # dump to stdout
sql-export gsheets -c config.yml [-r key:value ...]   # upload to Google Sheets
```

`gsheets` creates a new spreadsheet named `document_name`, one sheet per config entry, and opens the result URL in a browser. Requires an OAuth client secret file (see config below) and interactive consent on first run.

## Config file reference

### Screen dump

```yaml
database_type: mssql            # mssql or postgres
database:
  server: example.com
  port: 1433
  name: Northwind
  username: sa
  password: pass
sheets:
  - name: users
    query: "SELECT TOP 10 * FROM Users"
```

### Google Sheets export

```yaml
database_type: mssql            # mssql or postgres
database:
  server: example.com
  port: 1433
  name: Northwind
  username: sa
  password: pass
google_client_secret_file_path: ~/Downloads/client-secret.json   # gsheets only
document_name: My Export                                        # gsheets only
sheets:
  - name: users
    query: "SELECT TOP 10 * FROM Users"
```

```yaml
database_type: mssql            # mssql or postgres
database:
  server: example.com
  port: 1433
  name: Northwind
  username: sa
  password: pass
google_client_secret_file_path: ~/Downloads/client-secret.json   # gsheets only
document_name: My Export                                        # gsheets only
sheets:
  - name: users
    query: "SELECT TOP 10 * FROM Users"
    columns:                    # optional, gsheets only
      - index: 5                # zero-based column position
        data_type: date         # date or money ONLY — anything else fails at parse time
        format: dd-MM-yyyy       # cell display format
```

## Authoring / editing workflow

1. Draft or edit the config with the schema above.
2. Validate quickly without touching Google: `sql-export screen -c config.yml` — parse errors (bad `data_type`, duplicate YAML keys, malformed syntax) surface here.
3. Verify output looks correct on screen.
4. Publish: `sql-export gsheets -c config.yml`.

## Replacements

`-r key:value` replaces substrings in `query` strings before execution. Colons are allowed in values (e.g. `-r endpoint:https://example.com`). Duplicate keys are rejected. Longer keys are replaced first, so overlapping keys (e.g. `id` and `user_id`) behave deterministically.

## Troubleshooting

| Error | Cause |
|---|---|
| `unsupported data_type [x]` | Column `data_type` must be `date` or `money` |
| `invalid replacement "x"` | Missing `:` in a `-r` flag |
| `duplicated replacement key` | Same key passed twice via `-r` |
| YAML error with duplicate keys | yaml.v3 rejects duplicate mapping keys (unlike yaml.v2) |
| `configuration file is not specified` | Missing `-c` flag |
