"""Tests for io module."""

import numpy as np
import pytest

from weather_data_tool.io import (
    get_variable_metadata,
    infer_coord_names,
    load_dataset,
    normalize_longitude,
    save_dataset,
    spatial_subset,
)


def test_infer_coord_names(sample_dataset_small):
    """Test coordinate name inference."""
    coord_names = infer_coord_names(sample_dataset_small)

    assert "lat" in coord_names
    assert "lon" in coord_names
    assert coord_names["lat"] == "lat"
    assert coord_names["lon"] == "lon"


def test_infer_coord_names_alternative():
    """Test coordinate inference with alternative names."""
    import xarray as xr

    ds = xr.Dataset(
        {
            "temp": (["latitude", "longitude"], np.random.rand(5, 5)),
        },
        coords={
            "latitude": np.arange(5),
            "longitude": np.arange(5),
        },
    )

    coord_names = infer_coord_names(ds)
    assert coord_names["lat"] == "latitude"
    assert coord_names["lon"] == "longitude"


def test_normalize_longitude():
    """Test longitude normalization."""
    import xarray as xr

    # Create dataset with [0, 360] longitudes
    lons_360 = np.array([0, 90, 180, 270, 359])
    ds = xr.Dataset(
        {"temp": (["lon"], np.random.rand(5))},
        coords={"lon": lons_360},
    )

    ds_normalized = normalize_longitude(ds, "lon")

    # Check that longitudes are now in [-180, 180]
    assert ds_normalized.lon.min() >= -180
    assert ds_normalized.lon.max() <= 180


def test_spatial_subset(sample_dataset_medium):
    """Test spatial subsetting."""
    # Subset to a smaller region
    ds_subset = spatial_subset(
        sample_dataset_medium,
        lat_min=40.0,
        lat_max=45.0,
        lon_min=-5.0,
        lon_max=5.0,
    )

    # Check that subset is smaller
    assert len(ds_subset.lat) < len(sample_dataset_medium.lat)
    assert len(ds_subset.lon) < len(sample_dataset_medium.lon)

    # Check that bounds are correct
    assert ds_subset.lat.min() >= 40.0
    assert ds_subset.lat.max() <= 45.0
    assert ds_subset.lon.min() >= -5.0
    assert ds_subset.lon.max() <= 5.0

    # Check that variables are preserved
    assert "t2m" in ds_subset
    assert "u10" in ds_subset


def test_save_and_load_dataset(sample_dataset_small, tmp_output_dir):
    """Test saving and loading datasets."""
    output_file = tmp_output_dir / "test_dataset.nc"

    # Save
    save_dataset(sample_dataset_small, output_file, compression=True)

    # Check file exists
    assert output_file.exists()

    # Load
    ds_loaded = load_dataset(output_file)

    # Check data is the same
    assert "t2m" in ds_loaded
    np.testing.assert_allclose(
        ds_loaded.t2m.values,
        sample_dataset_small.t2m.values,
        rtol=1e-5,
    )

    # Check coordinates
    np.testing.assert_allclose(ds_loaded.lat.values, sample_dataset_small.lat.values)
    np.testing.assert_allclose(ds_loaded.lon.values, sample_dataset_small.lon.values)


def test_save_dataset_no_compression(sample_dataset_small, tmp_output_dir):
    """Test saving without compression."""
    output_file = tmp_output_dir / "test_no_compression.nc"

    save_dataset(sample_dataset_small, output_file, compression=False)

    assert output_file.exists()


def test_load_nonexistent_file(tmp_output_dir):
    """Test loading a file that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_dataset(tmp_output_dir / "nonexistent.nc")


def test_get_variable_metadata(sample_dataset_small):
    """Test extracting variable metadata."""
    metadata = get_variable_metadata(sample_dataset_small, "t2m")

    assert "long_name" in metadata
    assert "units" in metadata
    assert metadata["units"] == "K"


def test_get_variable_metadata_missing(sample_dataset_small):
    """Test metadata extraction for missing variable."""
    with pytest.raises(ValueError, match="not found"):
        get_variable_metadata(sample_dataset_small, "nonexistent_var")
