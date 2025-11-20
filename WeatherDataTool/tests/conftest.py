"""Pytest fixtures for WeatherDataTool tests."""

import numpy as np
import pytest
import xarray as xr


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "regions": {
            "test_region": {
                "lat_min": 40.0,
                "lat_max": 50.0,
                "lon_min": -10.0,
                "lon_max": 10.0,
            },
            "europe": {
                "lat_min": 30.0,
                "lat_max": 72.0,
                "lon_min": -25.0,
                "lon_max": 45.0,
            },
        },
        "reference_grids": {
            "test_grid": {
                "resolution": 1.0,
                "description": "Test grid 1 degree",
            },
            "gfs_0p25": {
                "resolution": 0.25,
                "description": "GFS 0.25 degree",
            },
        },
        "providers": {
            "test_provider": {
                "name": "Test Provider",
                "type": "opendap",
                "base_url": "http://test.example.com/data",
                "enabled": True,
                "variables": {
                    "t2m": "temperature",
                    "u10": "u_wind",
                    "v10": "v_wind",
                },
                "forecast_hours": [0, 6, 12, 24],
                "cycles": ["00", "06", "12", "18"],
            }
        },
        "defaults": {
            "provider": "test_provider",
            "reference_grid": "test_grid",
            "region": "test_region",
        },
    }


@pytest.fixture
def sample_dataset_small():
    """Create a small synthetic dataset (10x10 grid)."""
    # Create coordinates
    lats = np.linspace(40, 50, 10)
    lons = np.linspace(-10, 10, 10)

    # Create a simple linear temperature field
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    t2m_data = 273.15 + 10 + 0.5 * lat_grid + 0.3 * lon_grid  # Realistic temps in K

    # Create dataset
    ds = xr.Dataset(
        {
            "t2m": (["lat", "lon"], t2m_data),
        },
        coords={
            "lat": (["lat"], lats, {"units": "degrees_north", "long_name": "latitude"}),
            "lon": (["lon"], lons, {"units": "degrees_east", "long_name": "longitude"}),
        },
        attrs={
            "source": "test_dataset",
            "creation_date": "2024-01-01",
        },
    )

    # Add metadata to variable
    ds["t2m"].attrs = {
        "long_name": "2 metre temperature",
        "units": "K",
        "standard_name": "air_temperature",
    }

    return ds


@pytest.fixture
def sample_dataset_medium():
    """Create a medium synthetic dataset with multiple variables."""
    lats = np.linspace(35, 55, 20)
    lons = np.linspace(-15, 15, 30)

    lon_grid, lat_grid = np.meshgrid(lons, lats)

    # Temperature
    t2m = 273.15 + 10 + 0.5 * lat_grid + 0.3 * lon_grid

    # Wind components
    u10 = 5 + 0.1 * lon_grid
    v10 = 3 + 0.1 * lat_grid

    # Precipitation (always positive)
    tp = np.abs(0.1 * np.sin(lat_grid / 10) * np.cos(lon_grid / 10))

    ds = xr.Dataset(
        {
            "t2m": (["lat", "lon"], t2m),
            "u10": (["lat", "lon"], u10),
            "v10": (["lat", "lon"], v10),
            "tp": (["lat", "lon"], tp),
        },
        coords={
            "lat": (["lat"], lats, {"units": "degrees_north"}),
            "lon": (["lon"], lons, {"units": "degrees_east"}),
        },
    )

    # Add metadata
    ds["t2m"].attrs = {"long_name": "2m temperature", "units": "K"}
    ds["u10"].attrs = {"long_name": "10m u wind", "units": "m/s"}
    ds["v10"].attrs = {"long_name": "10m v wind", "units": "m/s"}
    ds["tp"].attrs = {"long_name": "total precipitation", "units": "mm"}

    return ds


@pytest.fixture
def sample_dataset_with_time():
    """Create a dataset with time dimension."""
    lats = np.linspace(40, 50, 10)
    lons = np.linspace(-10, 10, 10)
    times = np.arange(0, 5)  # 5 time steps

    # Create 3D data (time, lat, lon)
    t2m = np.zeros((len(times), len(lats), len(lons)))
    for t in range(len(times)):
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        t2m[t] = 273.15 + 10 + 0.5 * lat_grid + 0.3 * lon_grid + t

    ds = xr.Dataset(
        {
            "t2m": (["time", "lat", "lon"], t2m),
        },
        coords={
            "time": (["time"], times),
            "lat": (["lat"], lats),
            "lon": (["lon"], lons),
        },
    )

    ds["t2m"].attrs = {"long_name": "2m temperature", "units": "K"}

    return ds


@pytest.fixture
def sample_datasets_ensemble():
    """Create multiple datasets for ensemble testing."""
    lats = np.linspace(40, 50, 10)
    lons = np.linspace(-10, 10, 10)

    datasets = []

    # Create 3 ensemble members with slightly different values
    for i in range(3):
        lon_grid, lat_grid = np.meshgrid(lons, lats)

        # Add some variation between ensemble members
        t2m = 273.15 + 10 + 0.5 * lat_grid + 0.3 * lon_grid + i * 0.5
        t2m += np.random.normal(0, 0.2, t2m.shape)  # Add small noise

        ds = xr.Dataset(
            {
                "t2m": (["lat", "lon"], t2m),
            },
            coords={
                "lat": (["lat"], lats),
                "lon": (["lon"], lons),
            },
        )

        ds["t2m"].attrs = {"long_name": "2m temperature", "units": "K"}
        datasets.append(ds)

    return datasets


@pytest.fixture
def reference_grid_small():
    """Create a small reference grid for regridding tests."""
    lats = np.linspace(40, 50, 5)  # Coarser than sample_dataset_small
    lons = np.linspace(-10, 10, 5)

    ds = xr.Dataset(
        {
            "lat": (["lat"], lats),
            "lon": (["lon"], lons),
        }
    )

    return ds


@pytest.fixture
def reference_grid_different():
    """Create a reference grid with different extent."""
    lats = np.linspace(42, 48, 8)
    lons = np.linspace(-5, 5, 12)

    ds = xr.Dataset(
        {
            "lat": (["lat"], lats),
            "lon": (["lon"], lons),
        }
    )

    return ds


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
