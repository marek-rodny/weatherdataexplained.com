"""I/O utilities for reading and writing weather data."""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import xarray as xr

logger = logging.getLogger(__name__)


def infer_coord_names(ds: xr.Dataset) -> Dict[str, str]:
    """
    Infer coordinate names from dataset.

    Different datasets use different naming conventions (lat/latitude, lon/longitude, etc.).
    This function identifies the actual coordinate names.

    Args:
        ds: xarray Dataset

    Returns:
        Dictionary mapping standard names to actual coordinate names
    """
    coords = {}

    # Latitude
    for lat_name in ["latitude", "lat", "y", "rlat"]:
        if lat_name in ds.coords or lat_name in ds.dims:
            coords["lat"] = lat_name
            break

    # Longitude
    for lon_name in ["longitude", "lon", "x", "rlon"]:
        if lon_name in ds.coords or lon_name in ds.dims:
            coords["lon"] = lon_name
            break

    # Time
    for time_name in ["time", "valid_time", "forecast_time"]:
        if time_name in ds.coords or time_name in ds.dims:
            coords["time"] = time_name
            break

    logger.debug(f"Inferred coordinates: {coords}")
    return coords


def normalize_longitude(ds: xr.Dataset, lon_name: str = "lon") -> xr.Dataset:
    """
    Normalize longitude coordinates to [-180, 180] range.

    Args:
        ds: xarray Dataset
        lon_name: Name of longitude coordinate

    Returns:
        Dataset with normalized longitudes
    """
    if lon_name not in ds.coords:
        return ds

    lon_vals = ds[lon_name].values

    # Check if longitudes are in [0, 360] range
    if lon_vals.min() >= 0 and lon_vals.max() > 180:
        logger.debug("Converting longitudes from [0, 360] to [-180, 180]")
        ds = ds.assign_coords({lon_name: ((ds[lon_name] + 180) % 360) - 180})
        ds = ds.sortby(lon_name)

    return ds


def spatial_subset(
    ds: xr.Dataset,
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    coord_names: Optional[Dict[str, str]] = None,
) -> xr.Dataset:
    """
    Extract spatial subset from dataset.

    Args:
        ds: xarray Dataset
        lat_min: Minimum latitude
        lat_max: Maximum latitude
        lon_min: Minimum longitude
        lon_max: Maximum longitude
        coord_names: Optional coordinate name mapping

    Returns:
        Subsetted dataset
    """
    if coord_names is None:
        coord_names = infer_coord_names(ds)

    lat_name = coord_names.get("lat", "lat")
    lon_name = coord_names.get("lon", "lon")

    logger.info(f"Subsetting to lat=[{lat_min}, {lat_max}], lon=[{lon_min}, {lon_max}]")

    # Normalize longitudes if needed
    ds = normalize_longitude(ds, lon_name)

    # Perform selection
    subset = ds.sel(
        {
            lat_name: slice(lat_min, lat_max),
            lon_name: slice(lon_min, lon_max),
        }
    )

    logger.info(f"Subset shape: {dict(subset.sizes)}")
    return subset


def save_dataset(
    ds: xr.Dataset,
    output_path: Path,
    compression: bool = True,
    compression_level: int = 4,
) -> None:
    """
    Save dataset to NetCDF file with optional compression.

    Args:
        ds: xarray Dataset
        output_path: Output file path
        compression: Whether to apply compression
        compression_level: Compression level (1-9)
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    encoding = {}
    if compression:
        # Apply compression to all data variables
        for var in ds.data_vars:
            encoding[var] = {
                "zlib": True,
                "complevel": compression_level,
                "dtype": "float32",  # Save as float32 to reduce size
            }

    logger.info(f"Saving dataset to {output_path}")
    ds.to_netcdf(output_path, encoding=encoding, engine="netcdf4")

    # Report file size
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"Saved {file_size_mb:.2f} MB")


def load_dataset(file_path: Path) -> xr.Dataset:
    """
    Load dataset from NetCDF file.

    Args:
        file_path: Path to NetCDF file

    Returns:
        xarray Dataset
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Loading dataset from {file_path}")
    ds = xr.open_dataset(file_path, engine="netcdf4")

    logger.info(f"Loaded dataset with shape: {dict(ds.sizes)}")
    return ds


def get_variable_metadata(ds: xr.Dataset, var_name: str) -> Dict[str, str]:
    """
    Extract metadata for a variable.

    Args:
        ds: xarray Dataset
        var_name: Variable name

    Returns:
        Dictionary of metadata attributes
    """
    if var_name not in ds:
        raise ValueError(f"Variable {var_name} not found in dataset")

    var = ds[var_name]
    metadata = {
        "long_name": var.attrs.get("long_name", var_name),
        "units": var.attrs.get("units", "unknown"),
        "standard_name": var.attrs.get("standard_name", ""),
    }

    return metadata
