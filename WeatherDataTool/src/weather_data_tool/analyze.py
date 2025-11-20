"""Analysis functions for weather data comparison."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

logger = logging.getLogger(__name__)

# Try to import cartopy, but make it optional
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    CARTOPY_AVAILABLE = True
except ImportError:
    logger.warning("Cartopy not available. Maps will use basic matplotlib plotting.")
    CARTOPY_AVAILABLE = False


def compute_ensemble_spread(
    datasets: List[xr.Dataset],
    variable: str,
) -> Tuple[xr.DataArray, xr.DataArray, xr.DataArray]:
    """
    Compute ensemble spread (standard deviation) across multiple datasets.

    Args:
        datasets: List of xarray Datasets (must be on same grid)
        variable: Variable name to analyze

    Returns:
        Tuple of (mean, std_dev, max_spread_per_model)
    """
    logger.info(f"Computing ensemble spread for {len(datasets)} datasets")

    # Validate inputs
    if len(datasets) < 2:
        raise ValueError("Need at least 2 datasets to compute spread")

    # Check that all datasets have the same grid
    ref_shape = datasets[0].sizes
    for i, ds in enumerate(datasets[1:], 1):
        if ds.sizes != ref_shape:
            raise ValueError(
                f"Dataset {i} has different shape {ds.sizes} vs {ref_shape}"
            )

    # Check variable exists
    for i, ds in enumerate(datasets):
        if variable not in ds:
            raise ValueError(f"Variable {variable} not found in dataset {i}")

    # Stack datasets along a new 'model' dimension
    data_arrays = [ds[variable] for ds in datasets]
    stacked = xr.concat(data_arrays, dim="model")

    # Compute statistics
    ensemble_mean = stacked.mean(dim="model")
    ensemble_std = stacked.std(dim="model")

    logger.info(f"Ensemble spread computed: mean std = {float(ensemble_std.mean()):.3f}")

    return ensemble_mean, ensemble_std, stacked


def compute_pairwise_differences(
    datasets: List[xr.Dataset],
    variable: str,
    labels: Optional[List[str]] = None,
) -> Dict[str, xr.DataArray]:
    """
    Compute pairwise differences between datasets.

    Args:
        datasets: List of xarray Datasets
        variable: Variable name
        labels: Optional labels for each dataset

    Returns:
        Dictionary of difference arrays keyed by label pairs
    """
    if labels is None:
        labels = [f"Model_{i}" for i in range(len(datasets))]

    differences = {}

    for i in range(len(datasets)):
        for j in range(i + 1, len(datasets)):
            diff = datasets[i][variable] - datasets[j][variable]
            key = f"{labels[i]}_minus_{labels[j]}"
            differences[key] = diff

            logger.info(
                f"{key}: mean diff = {float(diff.mean()):.3f}, "
                f"max abs diff = {float(np.abs(diff).max()):.3f}"
            )

    return differences


def find_top_spread_locations(
    spread: xr.DataArray,
    top_n: int = 3,
) -> List[Dict]:
    """
    Find locations with highest spread.

    Args:
        spread: Spread (std dev) data array
        top_n: Number of top locations to return

    Returns:
        List of dictionaries with location info
    """
    # Flatten and find top values
    flat_spread = spread.values.flatten()
    flat_indices = np.argsort(flat_spread)[-top_n:][::-1]

    # Convert to 2D indices
    shape = spread.shape
    locations = []

    for flat_idx in flat_indices:
        idx_2d = np.unravel_index(flat_idx, shape)

        # Get coordinates
        lat_idx, lon_idx = idx_2d[-2], idx_2d[-1]  # Last two dims are lat, lon

        lat = float(spread.lat[lat_idx])
        lon = float(spread.lon[lon_idx])
        value = float(flat_spread[flat_idx])

        locations.append({
            "lat": lat,
            "lon": lon,
            "spread": value,
        })

    return locations


def create_spread_map(
    spread: xr.DataArray,
    output_path: Path,
    title: Optional[str] = None,
    variable_name: Optional[str] = None,
    units: Optional[str] = None,
) -> None:
    """
    Create a map visualization of ensemble spread.

    Args:
        spread: Spread data array (lat x lon)
        output_path: Output file path for PNG
        title: Plot title
        variable_name: Variable name for labeling
        units: Variable units for labeling
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Creating spread map: {output_path}")

    # Prepare title and labels
    if title is None:
        var_str = variable_name or "Variable"
        title = f"Ensemble Spread: {var_str}"

    cbar_label = "Spread (std dev)"
    if units:
        cbar_label += f" [{units}]"

    # Create figure
    if CARTOPY_AVAILABLE:
        fig = plt.figure(figsize=(12, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())

        # Add features
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle=":")
        ax.add_feature(cfeature.LAND, facecolor="lightgray", alpha=0.3)

        # Plot data
        im = ax.pcolormesh(
            spread.lon,
            spread.lat,
            spread,
            transform=ccrs.PlateCarree(),
            cmap="YlOrRd",
            shading="auto",
        )

        # Add gridlines
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5, linestyle="--")
        gl.top_labels = False
        gl.right_labels = False

    else:
        # Fallback: simple matplotlib plot
        fig, ax = plt.subplots(figsize=(12, 8))

        im = ax.pcolormesh(
            spread.lon,
            spread.lat,
            spread,
            cmap="YlOrRd",
            shading="auto",
        )

        ax.set_xlabel("Longitude (°E)")
        ax.set_ylabel("Latitude (°N)")
        ax.grid(True, alpha=0.3)
        ax.set_aspect("equal")

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, orientation="vertical", pad=0.05, shrink=0.8)
    cbar.set_label(cbar_label, fontsize=11)

    # Title
    plt.title(title, fontsize=14, fontweight="bold", pad=20)

    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    logger.info(f"Map saved to {output_path}")


def analyze_datasets(
    datasets: List[xr.Dataset],
    variable: str,
    labels: Optional[List[str]] = None,
    output_map: Optional[Path] = None,
) -> Dict:
    """
    Perform comprehensive analysis of multiple datasets.

    Args:
        datasets: List of datasets on the same grid
        variable: Variable to analyze
        labels: Labels for each dataset
        output_map: Optional path to save spread map

    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Analyzing {len(datasets)} datasets for variable: {variable}")

    if labels is None:
        labels = [f"Model_{i}" for i in range(len(datasets))]

    # Compute ensemble statistics
    ensemble_mean, ensemble_std, stacked = compute_ensemble_spread(datasets, variable)

    # Find top spread locations
    top_locations = find_top_spread_locations(ensemble_std, top_n=3)

    # Compute basic statistics for each dataset
    model_stats = []
    for i, (ds, label) in enumerate(zip(datasets, labels)):
        var_data = ds[variable]
        stats = {
            "label": label,
            "mean": float(var_data.mean()),
            "std": float(var_data.std()),
            "min": float(var_data.min()),
            "max": float(var_data.max()),
        }
        model_stats.append(stats)

    # Overall spread statistics
    spread_stats = {
        "mean_spread": float(ensemble_std.mean()),
        "max_spread": float(ensemble_std.max()),
        "min_spread": float(ensemble_std.min()),
    }

    # Create visualization if requested
    if output_map:
        # Get units from first dataset
        units = datasets[0][variable].attrs.get("units", "unknown")
        var_long_name = datasets[0][variable].attrs.get("long_name", variable)

        create_spread_map(
            ensemble_std,
            output_map,
            title=f"Ensemble Spread: {var_long_name}",
            variable_name=variable,
            units=units,
        )

    # Compile results
    results = {
        "variable": variable,
        "n_models": len(datasets),
        "spread_statistics": spread_stats,
        "top_spread_locations": top_locations,
        "model_statistics": model_stats,
    }

    return results


def print_analysis_summary(results: Dict) -> None:
    """
    Print a formatted summary of analysis results.

    Args:
        results: Results dictionary from analyze_datasets
    """
    print("\n" + "=" * 70)
    print("ENSEMBLE ANALYSIS SUMMARY")
    print("=" * 70)

    print(f"\nVariable: {results['variable']}")
    print(f"Number of models: {results['n_models']}")

    print("\n--- Spread Statistics ---")
    spread_stats = results["spread_statistics"]
    print(f"  Mean spread:   {spread_stats['mean_spread']:.4f}")
    print(f"  Max spread:    {spread_stats['max_spread']:.4f}")
    print(f"  Min spread:    {spread_stats['min_spread']:.4f}")

    print("\n--- Top 3 Locations with Highest Spread ---")
    for i, loc in enumerate(results["top_spread_locations"], 1):
        print(
            f"  {i}. Lat: {loc['lat']:7.2f}°, "
            f"Lon: {loc['lon']:7.2f}°, "
            f"Spread: {loc['spread']:.4f}"
        )

    print("\n--- Individual Model Statistics ---")
    for stats in results["model_statistics"]:
        print(f"\n  {stats['label']}:")
        print(f"    Mean: {stats['mean']:.4f}")
        print(f"    Std:  {stats['std']:.4f}")
        print(f"    Min:  {stats['min']:.4f}")
        print(f"    Max:  {stats['max']:.4f}")

    print("\n" + "=" * 70 + "\n")


def export_analysis_json(results: Dict, output_path: Path) -> None:
    """
    Export analysis results to JSON.

    Args:
        results: Results dictionary
        output_path: Output JSON file path
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Analysis results exported to {output_path}")
