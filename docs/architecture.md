# Architecture

```text
NYC OpenData API
      |
      v
Python Extract Script
      |
      v
Raw Data Layer (JSON)
      |
      v
Transform + Clean (pandas)
      |
      v
SQLite (incremental upsert)
      |
      v
Data Quality Checks (pytest + runtime checks)
      |
      v
Daily Markdown/HTML + Chart
      |
      v
GitHub Actions (daily schedule)
```

## Notes
- Incremental extraction uses `created_date > last_successful_loaded_timestamp`.
- `unique_key` is used as the upsert key in SQLite.
- Reports are versioned in `reports/` for portfolio visibility.

