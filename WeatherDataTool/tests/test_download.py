"""Tests for download module."""

from datetime import datetime

import pytest
import xarray as xr

from weather_data_tool.download import BaseProvider, get_provider


class MockProvider(BaseProvider):
    """Mock provider for testing."""

    def open_dataset(self, variable, forecast_hour, run_time=None):
        """Return a mock dataset."""
        import numpy as np

        lats = np.linspace(40, 50, 10)
        lons = np.linspace(-10, 10, 10)

        ds = xr.Dataset(
            {
                variable: (["lat", "lon"], np.random.rand(10, 10)),
            },
            coords={
                "lat": lats,
                "lon": lons,
            },
        )

        return ds


def test_base_provider_initialization(sample_config):
    """Test BaseProvider initialization."""
    provider_config = sample_config["providers"]["test_provider"]
    provider = MockProvider(provider_config)

    assert provider.name == "Test Provider"
    assert provider.provider_type == "opendap"
    assert provider.enabled is True


def test_get_variable_name(sample_config):
    """Test getting provider-specific variable name."""
    provider_config = sample_config["providers"]["test_provider"]
    provider = MockProvider(provider_config)

    # Standard to provider-specific mapping
    assert provider.get_variable_name("t2m") == "temperature"
    assert provider.get_variable_name("u10") == "u_wind"


def test_get_variable_name_invalid(sample_config):
    """Test error handling for invalid variable."""
    provider_config = sample_config["providers"]["test_provider"]
    provider = MockProvider(provider_config)

    with pytest.raises(ValueError, match="not available"):
        provider.get_variable_name("invalid_var")


def test_validate_forecast_hour(sample_config):
    """Test forecast hour validation."""
    provider_config = sample_config["providers"]["test_provider"]
    provider = MockProvider(provider_config)

    # Valid forecast hours
    provider.validate_forecast_hour(0)
    provider.validate_forecast_hour(6)
    provider.validate_forecast_hour(24)

    # Invalid forecast hour
    with pytest.raises(ValueError, match="not available"):
        provider.validate_forecast_hour(999)


def test_get_latest_run_time(sample_config):
    """Test getting latest run time."""
    provider_config = sample_config["providers"]["test_provider"]
    provider = MockProvider(provider_config)

    run_time = provider.get_latest_run_time()

    # Check that we get a datetime
    assert isinstance(run_time, datetime)

    # Check that hour is one of the cycles
    assert run_time.hour in [0, 6, 12, 18]

    # Check that minute/second/microsecond are zero
    assert run_time.minute == 0
    assert run_time.second == 0
    assert run_time.microsecond == 0


def test_mock_provider_open_dataset(sample_config):
    """Test mock provider dataset opening."""
    provider_config = sample_config["providers"]["test_provider"]
    provider = MockProvider(provider_config)

    ds = provider.open_dataset("t2m", 24)

    assert isinstance(ds, xr.Dataset)
    assert "t2m" in ds
    assert "lat" in ds.coords
    assert "lon" in ds.coords


def test_get_provider(sample_config):
    """Test provider factory function."""
    # This test validates the config structure
    # Actual provider classes require network access, so we test the logic

    # Test error for invalid provider name
    with pytest.raises(ValueError, match="not found"):
        get_provider("invalid_provider", sample_config)


def test_provider_enabled_flag(sample_config):
    """Test provider enabled flag."""
    # Add a disabled provider to config
    sample_config["providers"]["disabled_provider"] = {
        "name": "Disabled Provider",
        "type": "opendap",
        "enabled": False,
    }

    provider_config = sample_config["providers"]["disabled_provider"]
    provider = MockProvider(provider_config)

    assert provider.enabled is False
