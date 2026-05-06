from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

TABLE_NAME = "service_requests"


def initialize_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                unique_key INTEGER PRIMARY KEY,
                created_date TEXT NOT NULL,
                closed_date TEXT,
                agency TEXT,
                agency_name TEXT,
                complaint_type TEXT,
                descriptor TEXT,
                status TEXT,
                borough TEXT,
                incident_zip TEXT,
                latitude REAL,
                longitude REAL,
                loaded_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def upsert_dataframe(db_path: Path, df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    records = []
    for row in df.itertuples(index=False):
        records.append(
            (
                int(row.unique_key),
                row.created_date.isoformat() if pd.notna(row.created_date) else None,
                row.closed_date.isoformat() if pd.notna(row.closed_date) else None,
                _safe_str(row.agency),
                _safe_str(row.agency_name),
                _safe_str(row.complaint_type),
                _safe_str(row.descriptor),
                _safe_str(row.status),
                _safe_str(row.borough),
                _safe_str(row.incident_zip),
                _safe_float(row.latitude),
                _safe_float(row.longitude),
            )
        )

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            f"""
            INSERT INTO {TABLE_NAME} (
                unique_key, created_date, closed_date, agency, agency_name, complaint_type,
                descriptor, status, borough, incident_zip, latitude, longitude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(unique_key) DO UPDATE SET
                created_date = excluded.created_date,
                closed_date = excluded.closed_date,
                agency = excluded.agency,
                agency_name = excluded.agency_name,
                complaint_type = excluded.complaint_type,
                descriptor = excluded.descriptor,
                status = excluded.status,
                borough = excluded.borough,
                incident_zip = excluded.incident_zip,
                latitude = excluded.latitude,
                longitude = excluded.longitude;
            """,
            records,
        )
    return len(records)


def query_latest_metrics(db_path: Path) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(
            f"""
            SELECT
                DATE(created_date) AS request_date,
                COUNT(*) AS total_requests,
                COUNT(CASE WHEN status = 'Closed' THEN 1 END) AS closed_requests,
                COUNT(CASE WHEN status != 'Closed' THEN 1 END) AS open_requests
            FROM {TABLE_NAME}
            GROUP BY DATE(created_date)
            ORDER BY request_date DESC
            LIMIT 7;
            """,
            conn,
        )


def query_top_complaints(db_path: Path) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(
            f"""
            SELECT complaint_type, COUNT(*) AS count
            FROM {TABLE_NAME}
            WHERE DATE(created_date) = (
                SELECT DATE(MAX(created_date)) FROM {TABLE_NAME}
            )
            GROUP BY complaint_type
            ORDER BY count DESC
            LIMIT 10;
            """,
            conn,
        )


def query_borough_trends(db_path: Path) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(
            f"""
            SELECT
                DATE(created_date) AS request_date,
                borough,
                COUNT(*) AS count
            FROM {TABLE_NAME}
            WHERE borough IS NOT NULL
              AND DATE(created_date) >= DATE(
                    (SELECT MAX(created_date) FROM {TABLE_NAME}), '-6 days'
                  )
            GROUP BY DATE(created_date), borough
            ORDER BY request_date ASC;
            """,
            conn,
        )


def query_open_vs_closed(db_path: Path) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(
            f"""
            SELECT
                DATE(created_date) AS request_date,
                status,
                COUNT(*) AS count
            FROM {TABLE_NAME}
            WHERE DATE(created_date) >= DATE(
                    (SELECT MAX(created_date) FROM {TABLE_NAME}), '-6 days'
                  )
            GROUP BY DATE(created_date), status
            ORDER BY request_date ASC;
            """,
            conn,
        )


def query_top_agencies(db_path: Path) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(
            f"""
            SELECT agency_name, COUNT(*) AS count
            FROM {TABLE_NAME}
            WHERE DATE(created_date) = (
                SELECT DATE(MAX(created_date)) FROM {TABLE_NAME}
            )
              AND agency_name IS NOT NULL
            GROUP BY agency_name
            ORDER BY count DESC
            LIMIT 10;
            """,
            conn,
        )


def _safe_str(value: object) -> str | None:
    if pd.isna(value):
        return None
    return str(value)


def _safe_float(value: object) -> float | None:
    if pd.isna(value):
        return None
    return float(value)

