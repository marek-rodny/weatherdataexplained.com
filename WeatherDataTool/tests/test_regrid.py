"""Tests for regrid module."""

import numpy as np
import pytest

from weather_data_tool.regrid import (
    create_reference_grid,
    get_grid_from_config,
    prepare_dataset_for_regridding,
    regrid_dataset,
    regrid_to_common_grid,
)


def test_create_reference_grid():
    """Test creating a reference grid."""
    grid = create_reference_grid(
        lat_min=40.0,
        lat_max=50.0,
        lon_min=-10.0,
        lon_max=10.0,
        resolution=1.0,
    )

    assert "lat" in grid
    assert "lon" in grid

    # Check resolution
    lat_diff = np.diff(grid.lat.values)
    lon_diff = np.diff(grid.lon.values)

    np.testing.assert_allclose(lat_diff, 1.0, atol=0.01)
    np.testing.assert_allclose(lon_diff, 1.0, atol=0.01)

    # Check bounds
    assert grid.lat.min() >= 40.0
    assert grid.lat.max() <= 50.0
    assert grid.lon.min() >= -10.0
    assert grid.lon.max() <= 10.0


def test_get_grid_from_config(sample_config):
    """Test creating grid from configuration."""
    grid = get_grid_from_config(sample_config, "test_grid", "test_region")

    assert "lat" in grid
    assert "lon" in grid

    # Check resolution is 1.0 (from test_grid config)
    lat_diff = np.diff(grid.lat.values)
    np.testing.assert_allclose(lat_diff, 1.0, atol=0.01)


def test_get_grid_from_config_invalid_grid(sample_config):
    """Test error handling for invalid grid name."""
    with pytest.raises(ValueError, match="not found"):
        get_grid_from_config(sample_config, "invalid_grid", "test_region")


def test_get_grid_from_config_invalid_region(sample_config):
    """Test error handling for invalid region name."""
    with pytest.raises(ValueError, match="not found"):
        get_grid_from_config(sample_config, "test_grid", "invalid_region")


def test_prepare_dataset_for_regridding(sample_dataset_small):
    """Test dataset preparation for regridding."""
    ds_prep, coord_names = prepare_dataset_for_regridding(sample_dataset_small)

    assert "lat" in coord_names
    assert "lon" in coord_names


def test_regrid_dataset(sample_dataset_small, reference_grid_small):
    """Test regridding a dataset."""
    ds_regridded = regrid_dataset(
        sample_dataset_small,
        reference_grid_small,
        method="bilinear",
    )

    # Check that output has target grid dimensions
    assert len(ds_regridded.lat) == len(reference_grid_small.lat)
    assert len(ds_regridded.lon) == len(reference_grid_small.lon)

    # Check that variable is preserved
    assert "t2m" in ds_regridded

    # Check that values are reasonable (should be similar to original)
    assert ds_regridded.t2m.min() >= 273.15  # Above absolute zero
    assert ds_regridded.t2m.max() <= 330  # Below ~57°C

    # Check that regridding metadata is added
    assert "regrid_method" in ds_regridded.attrs


def test_regrid_dataset_nearest(sample_dataset_small, reference_grid_small):
    """Test regridding with nearest neighbor method."""
    ds_regridded = regrid_dataset(
        sample_dataset_small,
        reference_grid_small,
        method="nearest_s2d",
    )

    assert len(ds_regridded.lat) == len(reference_grid_small.lat)
    assert "t2m" in ds_regridded
    assert ds_regridded.attrs["regrid_method"] == "nearest_s2d"


def test_regrid_to_common_grid(sample_datasets_ensemble, reference_grid_small):
    """Test regridding multiple datasets to common grid."""
    datasets_regridded = regrid_to_common_grid(
        sample_datasets_ensemble,
        reference_grid_small,
        method="bilinear",
    )

    assert len(datasets_regridded) == len(sample_datasets_ensemble)

    # Check that all have same grid
    for ds in datasets_regridded:
        assert len(ds.lat) == len(reference_grid_small.lat)
        assert len(ds.lon) == len(reference_grid_small.lon)

    # Check that all lat/lon coordinates match
    for i in range(1, len(datasets_regridded)):
        np.testing.assert_array_equal(
            datasets_regridded[i].lat.values,
            datasets_regridded[0].lat.values,
        )
        np.testing.assert_array_equal(
            datasets_regridded[i].lon.values,
            datasets_regridded[0].lon.values,
        )


def test_regrid_preserves_attributes(sample_dataset_small, reference_grid_small):
    """Test that regridding preserves important attributes."""
    # Add some custom attributes
    sample_dataset_small.attrs["model"] = "TEST_MODEL"
    sample_dataset_small["t2m"].attrs["custom_attr"] = "test_value"

    ds_regridded = regrid_dataset(
        sample_dataset_small,
        reference_grid_small,
        method="bilinear",
    )

    # Check global attributes are preserved
    assert "model" in ds_regridded.attrs
    assert ds_regridded.attrs["model"] == "TEST_MODEL"
