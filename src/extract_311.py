from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from src.config import AppConfig

SELECT_COLUMNS = (
    "unique_key,created_date,closed_date,agency,agency_name,complaint_type,"
    "descriptor,status,borough,incident_zip,latitude,longitude"
)


def read_last_successful_timestamp(state_file_path: Path) -> str:
    if state_file_path.exists():
        return state_file_path.read_text(encoding="utf-8").strip()

    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    return yesterday.isoformat(timespec="seconds")


def save_last_successful_timestamp(state_file_path: Path, timestamp_iso: str) -> None:
    state_file_path.write_text(timestamp_iso, encoding="utf-8")


def fetch_incremental_data(cfg: AppConfig, created_after_iso: str) -> list[dict]:
    all_rows: list[dict] = []
    soql_datetime = _to_soql_datetime(created_after_iso)

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if cfg.app_token:
        headers["X-App-Token"] = cfg.app_token

    # Keep the secret token available for future auth changes without sending unknown headers.
    _ = cfg.secret_token

    for page in range(cfg.max_pages):
        offset = page * cfg.page_size
        query = (
            f"SELECT {SELECT_COLUMNS} "
            f"WHERE created_date > '{soql_datetime}' "
            "ORDER BY created_date ASC "
            f"LIMIT {cfg.page_size} OFFSET {offset}"
        )

        params = {
            "pageNumber": page + 1,
            "pageSize": cfg.page_size,
        }
        if cfg.app_token:
            params["app_token"] = cfg.app_token

        response = requests.post(
            cfg.api_endpoint,
            params=params,
            headers=headers,
            json={"query": query},
            timeout=60,
        )
        response.raise_for_status()

        page_rows = _extract_rows(response.json())
        if not page_rows:
            break

        all_rows.extend(page_rows)

        if len(page_rows) < cfg.page_size:
            break

    return all_rows


def save_raw_payload(raw_data_dir: Path, rows: list[dict]) -> Path:
    run_ts = datetime.now(timezone.utc).strftime("%Y_%m_%d")
    output_path = raw_data_dir / f"311_requests_{run_ts}.json"

    import json

    output_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return output_path


def _extract_rows(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]

    if isinstance(payload, dict):
        for key in ("results", "data", "rows"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]

    return []


def _to_soql_datetime(timestamp_iso: str) -> str:
    ts = timestamp_iso.strip().lstrip("\ufeff").replace("Z", "+00:00")
    parsed = datetime.fromisoformat(ts)
    parsed_utc = parsed.astimezone(timezone.utc)
    return parsed_utc.strftime("%Y-%m-%dT%H:%M:%S")
