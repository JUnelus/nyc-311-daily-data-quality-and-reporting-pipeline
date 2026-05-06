from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture()
def sample_rows() -> list[dict]:
    return [
        {
            "unique_key": "1001",
            "created_date": "2026-05-04T11:00:00.000",
            "closed_date": "2026-05-04T14:00:00.000",
            "agency": "NYPD",
            "agency_name": "Police Department",
            "complaint_type": "Noise - Residential",
            "descriptor": "Loud Music/Party",
            "status": "Closed",
            "borough": "BROOKLYN",
            "incident_zip": "11201",
            "latitude": "40.6943",
            "longitude": "-73.9928",
        },
        {
            "unique_key": "1002",
            "created_date": "2026-05-04T12:00:00.000",
            "closed_date": None,
            "agency": "DOT",
            "agency_name": "Department of Transportation",
            "complaint_type": "Street Condition",
            "descriptor": "Pothole",
            "status": "Open",
            "borough": "MANHATTAN",
            "incident_zip": "10001",
            "latitude": "40.7505",
            "longitude": "-73.9965",
        },
    ]


@pytest.fixture()
def sample_df(sample_rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(sample_rows)

