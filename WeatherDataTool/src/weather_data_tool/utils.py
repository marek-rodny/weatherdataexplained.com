"""Utility functions for WeatherDataTool."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, uses default config.yaml

    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Default to configs/config.yaml relative to package
        package_dir = Path(__file__).parent.parent.parent
        config_path = package_dir / "configs" / "config.yaml"

    logger.debug(f"Loading configuration from {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """
    Parse ISO datetime string.

    Args:
        dt_str: ISO format datetime string (e.g., "2024-01-15T12:00:00")

    Returns:
        datetime object or None
    """
    if dt_str is None:
        return None

    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        logger.error(f"Invalid datetime format: {dt_str}")
        raise


def format_run_time(dt: datetime) -> str:
    """
    Format datetime for use in file paths and URLs.

    Args:
        dt: datetime object

    Returns:
        Formatted string (YYYYMMDD)
    """
    return dt.strftime("%Y%m%d")


def get_cycle_hour(dt: datetime) -> str:
    """
    Get the cycle hour from a datetime.

    Args:
        dt: datetime object

    Returns:
        Two-digit cycle hour string (e.g., "00", "06", "12", "18")
    """
    return f"{dt.hour:02d}"


def validate_bounds(lat_min: float, lat_max: float, lon_min: float, lon_max: float) -> None:
    """
    Validate spatial bounds.

    Args:
        lat_min: Minimum latitude
        lat_max: Maximum latitude
        lon_min: Minimum longitude
        lon_max: Maximum longitude

    Raises:
        ValueError: If bounds are invalid
    """
    if not (-90 <= lat_min < lat_max <= 90):
        raise ValueError(f"Invalid latitude bounds: {lat_min}, {lat_max}")

    if not (-180 <= lon_min < lon_max <= 360):
        raise ValueError(f"Invalid longitude bounds: {lon_min}, {lon_max}")


def ensure_dir(path: Path) -> None:
    """
    Ensure directory exists, create if necessary.

    Args:
        path: Directory path
    """
    path.mkdir(parents=True, exist_ok=True)
