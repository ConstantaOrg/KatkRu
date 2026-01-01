import pytest

from core.utils.anything import hide_log_param, extract_conflict_values


def test_hide_log_param_masks_middle():
    masked = hide_log_param("password", start=2, end=2)
    assert masked.startswith("pa")
    assert masked.endswith("rd")
    # middle characters are replaced with asterisks
    assert masked == "pa***rd"


def test_extract_conflict_values_parses_pairs():
    detail = "dup (1,2) more (3,4) trailing"
    parsed = extract_conflict_values(detail)
    assert parsed == [("1", "2"), ("3", "4")]
