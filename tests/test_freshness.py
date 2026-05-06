from datetime import datetime, timedelta, timezone

from src.extract_311 import read_last_successful_timestamp


def test_default_freshness_when_state_file_missing(tmp_path):
    state_file = tmp_path / "missing_state.txt"
    ts = read_last_successful_timestamp(state_file)
    parsed = datetime.fromisoformat(ts)

    delta = datetime.now(timezone.utc) - parsed
    assert timedelta(hours=12) <= delta <= timedelta(days=2)

