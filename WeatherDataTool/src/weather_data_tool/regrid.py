"""Regridding utilities using xESMF."""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import xarray as xr
import xesmf as xe

from weather_data_tool.io import infer_coord_names

logger = logging.getLogger(__name__)


def create_reference_grid(
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    resolution: float,
) -> xr.Dataset:
    """
    Create a regular lat-lon reference grid.

    Args:
        lat_min: Minimum latitude
        lat_max: Maximum latitude
        lon_min: Minimum longitude
        lon_max: Maximum longitude
        resolution: Grid resolution in degrees

    Returns:
        xarray Dataset with lat/lon coordinates
    """
    logger.info(
        f"Creating reference grid: "
        f"lat=[{lat_min}, {lat_max}], lon=[{lon_min}, {lon_max}], "
        f"resolution={resolution}°"
    )

    # Create coordinate arrays
    lats = np.arange(lat_min, lat_max + resolution, resolution)
    lons = np.arange(lon_min, lon_max + resolution, resolution)

    # Create grid dataset
    ds_grid = xr.Dataset(
        {
            "lat": (["lat"], lats, {"units": "degrees_north", "long_name": "latitude"}),
            "lon": (["lon"], lons, {"units": "degrees_east", "long_name": "longitude"}),
        }
    )

    logger.info(f"Created grid with shape: lat={len(lats)}, lon={len(lons)}")
    return ds_grid


def get_grid_from_config(config: Dict, grid_name: str, region_name: str) -> xr.Dataset:
    """
    Create a reference grid from configuration.

    Args:
        config: Configuration dictionary
        grid_name: Name of reference grid (e.g., 'gfs_0p25')
        region_name: Name of region (e.g., 'europe')

    Returns:
        xarray Dataset with reference grid
    """
    grids_config = config.get("reference_grids", {})
    regions_config = config.get("regions", {})

    if grid_name not in grids_config:
        available = list(grids_config.keys())
        raise ValueError(f"Grid {grid_name} not found. Available: {available}")

    if region_name not in regions_config:
        available = list(regions_config.keys())
        raise ValueError(f"Region {region_name} not found. Available: {available}")

    grid_config = grids_config[grid_name]
    region_config = regions_config[region_name]

    resolution = grid_config["resolution"]

    return create_reference_grid(
        lat_min=region_config["lat_min"],
        lat_max=region_config["lat_max"],
        lon_min=region_config["lon_min"],
        lon_max=region_config["lon_max"],
        resolution=resolution,
    )


def prepare_dataset_for_regridding(ds: xr.Dataset) -> Tuple[xr.Dataset, Dict[str, str]]:
    """
    Prepare dataset for regridding by standardizing coordinate names.

    Args:
        ds: Input dataset

    Returns:
        Tuple of (prepared dataset, coordinate name mapping)
    """
    coord_names = infer_coord_names(ds)

    # Rename coordinates to standard names if needed
    rename_dict = {}
    if coord_names.get("lat") and coord_names["lat"] != "lat":
        rename_dict[coord_names["lat"]] = "lat"
    if coord_names.get("lon") and coord_names["lon"] != "lon":
        rename_dict[coord_names["lon"]] = "lon"

    if rename_dict:
        logger.debug(f"Renaming coordinates: {rename_dict}")
        ds = ds.rename(rename_dict)

    return ds, coord_names


def regrid_dataset(
    ds_in: xr.Dataset,
    ds_target: xr.Dataset,
    method: str = "bilinear",
    periodic: bool = False,
    reuse_weights: bool = True,
    weights_dir: Optional[Path] = None,
) -> xr.Dataset:
    """
    Regrid dataset to target grid using xESMF.

    Args:
        ds_in: Input dataset to regrid
        ds_target: Target grid dataset (or dataset with target grid)
        method: Regridding method ('bilinear', 'conservative', 'nearest_s2d', 'nearest_d2s')
        periodic: Whether longitude is periodic (wraps at 360°)
        reuse_weights: Whether to reuse weights if available
        weights_dir: Directory to store/load regridding weights

    Returns:
        Regridded dataset
    """
    logger.info(f"Starting regridding with method: {method}")

    # Prepare source dataset
    ds_in_prep, _ = prepare_dataset_for_regridding(ds_in)
    ds_target_prep, _ = prepare_dataset_for_regridding(ds_target)

    # Log grid info
    logger.info(
        f"Source grid: lat={len(ds_in_prep.lat)}, lon={len(ds_in_prep.lon)}"
    )
    logger.info(
        f"Target grid: lat={len(ds_target_prep.lat)}, lon={len(ds_target_prep.lon)}"
    )

    # Create regridder
    try:
        # Build weights filename for caching
        weights_filename = None
        if reuse_weights and weights_dir:
            weights_dir = Path(weights_dir)
            weights_dir.mkdir(parents=True, exist_ok=True)

            src_shape = f"{len(ds_in_prep.lat)}x{len(ds_in_prep.lon)}"
            tgt_shape = f"{len(ds_target_prep.lat)}x{len(ds_target_prep.lon)}"
            weights_filename = (
                weights_dir / f"weights_{method}_{src_shape}_to_{tgt_shape}.nc"
            )

        logger.info("Building regridder (this may take a moment on first run)...")

        regridder = xe.Regridder(
            ds_in_prep,
            ds_target_prep,
            method=method,
            periodic=periodic,
            reuse_weights=reuse_weights,
            filename=str(weights_filename) if weights_filename else None,
        )

        logger.info("Regridder created successfully")

        # Apply regridding to all data variables
        ds_out = regridder(ds_in_prep, keep_attrs=True)

        logger.info(f"Regridding complete. Output shape: {dict(ds_out.sizes)}")

        # Copy global attributes
        ds_out.attrs.update(ds_in.attrs)
        ds_out.attrs["regrid_method"] = method
        ds_out.attrs["regrid_source_shape"] = str(dict(ds_in_prep.sizes))
        ds_out.attrs["regrid_target_shape"] = str(dict(ds_target_prep.sizes))

        return ds_out

    except Exception as e:
        logger.error(f"Regridding failed: {e}")
        raise RuntimeError(f"Failed to regrid dataset: {e}")


def regrid_to_common_grid(
    datasets: list[xr.Dataset],
    reference_grid: xr.Dataset,
    method: str = "bilinear",
) -> list[xr.Dataset]:
    """
    Regrid multiple datasets to a common grid.

    Args:
        datasets: List of datasets to regrid
        reference_grid: Common target grid
        method: Regridding method

    Returns:
        List of regridded datasets
    """
    logger.info(f"Regridding {len(datasets)} datasets to common grid")

    regridded = []
    for i, ds in enumerate(datasets):
        logger.info(f"Regridding dataset {i+1}/{len(datasets)}")
        ds_regridded = regrid_dataset(ds, reference_grid, method=method)
        regridded.append(ds_regridded)

    return regridded
