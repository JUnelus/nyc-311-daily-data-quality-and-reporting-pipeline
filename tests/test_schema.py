from src.transform_311 import REQUIRED_COLUMNS, transform_rows


def test_transform_returns_expected_schema(sample_rows):
    df = transform_rows(sample_rows)
    assert list(df.columns) == REQUIRED_COLUMNS
    assert len(df) == 2
    assert str(df["created_date"].dtype).startswith("datetime64")

