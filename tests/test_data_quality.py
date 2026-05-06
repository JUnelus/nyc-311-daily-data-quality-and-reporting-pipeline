from src.generate_report import run_data_quality_checks
from src.transform_311 import transform_rows


def test_data_quality_passes_for_valid_data(sample_rows):
    df = transform_rows(sample_rows)
    failures = run_data_quality_checks(df)
    assert failures == []


def test_data_quality_flags_invalid_borough(sample_rows):
    sample_rows[0]["borough"] = "NOT_A_BOROUGH"
    df = transform_rows(sample_rows)
    failures = run_data_quality_checks(df)
    assert any("borough" in f for f in failures)

