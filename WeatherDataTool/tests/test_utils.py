"""Tests for utils module."""

from datetime import datetime
from pathlib import Path

import pytest

from weather_data_tool.utils import (
    ensure_dir,
    format_run_time,
    get_cycle_hour,
    parse_datetime,
    validate_bounds,
)


def test_parse_datetime():
    """Test datetime parsing."""
    dt = parse_datetime("2024-01-15T12:00:00")

    assert isinstance(dt, datetime)
    assert dt.year == 2024
    assert dt.month == 1
    assert dt.day == 15
    assert dt.hour == 12


def test_parse_datetime_with_z():
    """Test parsing datetime with Z suffix."""
    dt = parse_datetime("2024-01-15T12:00:00Z")

    assert isinstance(dt, datetime)
    assert dt.year == 2024


def test_parse_datetime_none():
    """Test parsing None."""
    dt = parse_datetime(None)
    assert dt is None


def test_parse_datetime_invalid():
    """Test parsing invalid datetime string."""
    with pytest.raises(ValueError):
        parse_datetime("not-a-datetime")


def test_format_run_time():
    """Test datetime formatting for file paths."""
    dt = datetime(2024, 1, 15, 12, 30, 45)
    formatted = format_run_time(dt)

    assert formatted == "20240115"


def test_get_cycle_hour():
    """Test getting cycle hour from datetime."""
    dt = datetime(2024, 1, 15, 6, 0, 0)
    cycle = get_cycle_hour(dt)

    assert cycle == "06"

    dt = datetime(2024, 1, 15, 18, 30, 0)
    cycle = get_cycle_hour(dt)

    assert cycle == "18"


def test_validate_bounds_valid():
    """Test validating correct bounds."""
    # Should not raise
    validate_bounds(30, 60, -20, 40)
    validate_bounds(-90, 90, -180, 180)
    validate_bounds(0, 45, 0, 90)


def test_validate_bounds_invalid_lat():
    """Test invalid latitude bounds."""
    with pytest.raises(ValueError, match="Invalid latitude"):
        validate_bounds(-100, 60, -20, 40)

    with pytest.raises(ValueError, match="Invalid latitude"):
        validate_bounds(30, 100, -20, 40)

    with pytest.raises(ValueError, match="Invalid latitude"):
        validate_bounds(60, 30, -20, 40)  # lat_min > lat_max


def test_validate_bounds_invalid_lon():
    """Test invalid longitude bounds."""
    with pytest.raises(ValueError, match="Invalid longitude"):
        validate_bounds(30, 60, -200, 40)

    with pytest.raises(ValueError, match="Invalid longitude"):
        validate_bounds(30, 60, -20, 400)

    with pytest.raises(ValueError, match="Invalid longitude"):
        validate_bounds(30, 60, 40, 20)  # lon_min > lon_max


def test_ensure_dir(tmp_path):
    """Test directory creation."""
    test_dir = tmp_path / "new_dir" / "nested_dir"

    assert not test_dir.exists()

    ensure_dir(test_dir)

    assert test_dir.exists()
    assert test_dir.is_dir()


def test_ensure_dir_existing(tmp_path):
    """Test ensure_dir with existing directory."""
    test_dir = tmp_path / "existing_dir"
    test_dir.mkdir()

    # Should not raise
    ensure_dir(test_dir)

    assert test_dir.exists()
