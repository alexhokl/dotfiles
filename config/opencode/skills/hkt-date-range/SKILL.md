---
name: hkt-date-range
description: Use when you need the current bi-weekly reporting window in HKT (Hong Kong Time). Provides start_time and end_time as a 14-day range ending on the most recent Monday midnight. Trigger keywords: date range, HKT, biweekly, reporting period, start time, end time, two weeks.
---

# HKT Bi-Weekly Date Range

Computes a 14-day reporting window anchored to the most recent Monday at 00:00:00 HKT.

## When to use

- The user asks for a "reporting period", "biweekly window", or "last two weeks" in HKT.
- You need `start_time` / `end_time` to filter or scope a query.

## How to use

Run the bundled script with the Bash tool:

```bash
bash ~/.config/opencode/skills/hkt-date-range/handler.sh
```

Parse the JSON response:

```json
{
  "status": "success",
  "timezone": "HKT",
  "start_time": "2026-05-18 00:00:00",
  "end_time": "2026-06-01 00:00:00"
}
```

Use `start_time` and `end_time` in downstream queries or task context.

## Notes

- Requires `gdate` (GNU date). Install with: `brew install coreutils`.
- `end_time` is the most recent Monday at midnight HKT.
- `start_time` is exactly 14 days prior.
- If today is Monday, `end_time` is today's midnight — the new window just opened.
