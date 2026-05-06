from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = [
    "unique_key",
    "created_date",
    "closed_date",
    "agency",
    "agency_name",
    "complaint_type",
    "descriptor",
    "status",
    "borough",
    "incident_zip",
    "latitude",
    "longitude",
]


def transform_rows(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    df = pd.DataFrame(rows)

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[REQUIRED_COLUMNS].copy()

    df["unique_key"] = pd.to_numeric(df["unique_key"], errors="coerce").astype("Int64")
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce", utc=True)
    df["closed_date"] = pd.to_datetime(df["closed_date"], errors="coerce", utc=True)

    for str_col in ["agency", "agency_name", "complaint_type", "descriptor", "status", "borough", "incident_zip"]:
        df[str_col] = df[str_col].astype("string").str.strip()

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    df = df.dropna(subset=["unique_key", "created_date"]).drop_duplicates(subset=["unique_key"], keep="last")
    return df

