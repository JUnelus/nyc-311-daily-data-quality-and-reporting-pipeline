from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from src.config import AppConfig, ensure_directories
from src.extract_311 import (
    fetch_incremental_data,
    read_last_successful_timestamp,
    save_last_successful_timestamp,
    save_raw_payload,
)
from src.generate_report import generate_outputs, run_data_quality_checks, update_readme
from src.load_311 import (
    TABLE_NAME,
    initialize_database,
    query_borough_trends,
    query_latest_metrics,
    query_open_vs_closed,
    query_top_agencies,
    query_top_complaints,
    upsert_dataframe,
)
from src.transform_311 import transform_rows


def run_pipeline() -> None:
    cfg = AppConfig()
    ensure_directories(cfg)

    initialize_database(cfg.sqlite_db_path)
    last_loaded = read_last_successful_timestamp(cfg.state_file_path)

    rows = fetch_incremental_data(cfg, last_loaded)
    raw_path = save_raw_payload(cfg.raw_data_dir, rows)

    df = transform_rows(rows)
    failures = run_data_quality_checks(df)

    inserted = upsert_dataframe(cfg.sqlite_db_path, df)

    metrics_df = query_latest_metrics(cfg.sqlite_db_path)
    complaints_df = query_top_complaints(cfg.sqlite_db_path)
    borough_trends_df = query_borough_trends(cfg.sqlite_db_path)
    open_vs_closed_df = query_open_vs_closed(cfg.sqlite_db_path)
    top_agencies_df = query_top_agencies(cfg.sqlite_db_path)

    generate_outputs(
        metrics_df=metrics_df,
        complaints_df=complaints_df,
        borough_trends_df=borough_trends_df,
        open_vs_closed_df=open_vs_closed_df,
        top_agencies_df=top_agencies_df,
        quality_failures=failures,
        markdown_path=cfg.daily_summary_md_path,
        metrics_csv_path=cfg.latest_metrics_csv_path,
        html_path=cfg.latest_report_html_path,
        charts_dir=cfg.charts_dir,
    )

    update_readme(
        readme_path=cfg.project_root / "README.md",
        metrics_df=metrics_df,
        quality_failures=failures,
    )

    if not df.empty:
        newest_ts = df["created_date"].max().to_pydatetime().astimezone(timezone.utc).isoformat(timespec="seconds")
        save_last_successful_timestamp(cfg.state_file_path, newest_ts)

    print(f"Pulled rows   : {len(rows)}")
    print(f"Upserted rows : {inserted}")
    print(f"Raw payload   : {raw_path}")
    print(f"Daily report  : {cfg.daily_summary_md_path}")
    print(f"HTML report   : {cfg.latest_report_html_path}")
    print(f"Charts        : {cfg.charts_dir}")
    print(f"README updated: {cfg.project_root / 'README.md'}")


if __name__ == "__main__":
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"Starting NYC 311 pipeline run at {now}")
    run_pipeline()
