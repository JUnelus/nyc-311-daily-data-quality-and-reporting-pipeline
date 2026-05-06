from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_local_env(project_root: Path) -> None:
    """Load key/value pairs from .env for local development without extra dependencies."""
    env_path = project_root / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
_load_local_env(PROJECT_ROOT)


@dataclass(frozen=True)
class AppConfig:
    """Central configuration for local runs and GitHub Actions."""

    api_endpoint: str = os.getenv(
        "NYC311_API_ENDPOINT", "https://data.cityofnewyork.us/api/v3/views/erm2-nwe9/query.json"
    )
    app_token: str | None = os.getenv("NYC311_APP_TOKEN")
    secret_token: str | None = os.getenv("NYC311_SECRET_TOKEN")
    page_size: int = int(os.getenv("NYC311_PAGE_SIZE", "50000"))
    max_pages: int = int(os.getenv("NYC311_MAX_PAGES", "5"))

    project_root: Path = PROJECT_ROOT
    raw_data_dir: Path = project_root / "data" / "raw"
    processed_data_dir: Path = project_root / "data" / "processed"
    sqlite_db_path: Path = project_root / "data" / "processed" / "nyc311.db"
    state_file_path: Path = project_root / "data" / "processed" / "last_successful_load.txt"

    reports_dir: Path = project_root / "reports"
    charts_dir: Path = project_root / "reports" / "charts"
    daily_summary_md_path: Path = project_root / "reports" / "daily_summary.md"
    latest_metrics_csv_path: Path = project_root / "reports" / "latest_metrics.csv"
    latest_report_html_path: Path = project_root / "reports" / "daily_summary.html"


def ensure_directories(cfg: AppConfig) -> None:
    cfg.raw_data_dir.mkdir(parents=True, exist_ok=True)
    cfg.processed_data_dir.mkdir(parents=True, exist_ok=True)
    cfg.reports_dir.mkdir(parents=True, exist_ok=True)
    cfg.charts_dir.mkdir(parents=True, exist_ok=True)
