"""Command-line interface for WeatherDataTool."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click

from weather_data_tool.analyze import (
    analyze_datasets,
    export_analysis_json,
    print_analysis_summary,
)
from weather_data_tool.download import get_provider
from weather_data_tool.io import load_dataset, save_dataset, spatial_subset
from weather_data_tool.regrid import (
    create_reference_grid,
    get_grid_from_config,
    regrid_dataset,
)
from weather_data_tool.utils import load_config, parse_datetime, setup_logging, validate_bounds

logger = logging.getLogger(__name__)


@click.group()
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Logging level",
)
@click.pass_context
def cli(ctx, log_level: str):
    """WeatherDataTool: Download, regrid, and analyze weather forecast data."""
    setup_logging(log_level)
    ctx.ensure_object(dict)

    # Load configuration
    try:
        config = load_config()
        ctx.obj["config"] = config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--provider",
    required=True,
    help="Data provider name (e.g., 'gfs_opendap', 'hrrr_zarr')",
)
@click.option(
    "--variable",
    required=True,
    help="Variable name (e.g., 't2m', 'u10', 'v10')",
)
@click.option(
    "--forecast-hour",
    type=int,
    required=True,
    help="Forecast hour (e.g., 24 for +24h forecast)",
)
@click.option(
    "--run-time",
    type=str,
    help="Model run time in ISO format (e.g., '2024-01-15T12:00:00'). If not provided, uses latest.",
)
@click.option(
    "--region",
    type=str,
    help="Region name from config (e.g., 'europe', 'conus')",
)
@click.option(
    "--bounds",
    type=str,
    help="Custom bounds as 'lat_min,lat_max,lon_min,lon_max'",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file path. If not provided, uses automatic naming in data/raw/",
)
@click.pass_context
def download(
    ctx,
    provider: str,
    variable: str,
    forecast_hour: int,
    run_time: Optional[str],
    region: Optional[str],
    bounds: Optional[str],
    output: Optional[str],
):
    """Download weather data from a provider."""
    config = ctx.obj["config"]

    try:
        # Parse run time if provided
        run_time_dt = parse_datetime(run_time) if run_time else None

        # Get provider
        logger.info(f"Initializing provider: {provider}")
        data_provider = get_provider(provider, config)

        # Open dataset
        logger.info(f"Downloading {variable} at forecast hour {forecast_hour}")
        ds = data_provider.open_dataset(variable, forecast_hour, run_time_dt)

        # Apply spatial subset if requested
        if region or bounds:
            if region:
                regions_config = config["regions"]
                if region not in regions_config:
                    raise ValueError(f"Region {region} not found in config")
                region_config = regions_config[region]
                lat_min = region_config["lat_min"]
                lat_max = region_config["lat_max"]
                lon_min = region_config["lon_min"]
                lon_max = region_config["lon_max"]
            else:
                # Parse bounds string
                parts = bounds.split(",")
                if len(parts) != 4:
                    raise ValueError("Bounds must be 'lat_min,lat_max,lon_min,lon_max'")
                lat_min, lat_max, lon_min, lon_max = map(float, parts)

            validate_bounds(lat_min, lat_max, lon_min, lon_max)
            ds = spatial_subset(ds, lat_min, lat_max, lon_min, lon_max)

        # Determine output path
        if output:
            output_path = Path(output)
        else:
            # Auto-generate filename
            package_dir = Path(__file__).parent.parent.parent
            output_dir = package_dir / "data" / "raw"
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{provider}_{variable}_f{forecast_hour:03d}.nc"
            output_path = output_dir / filename

        # Save dataset
        save_dataset(ds, output_path)

        click.echo(f"✓ Successfully downloaded data to: {output_path}")

    except Exception as e:
        logger.error(f"Download failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--source",
    type=click.Path(exists=True),
    required=True,
    help="Source NetCDF file to regrid",
)
@click.option(
    "--target-grid",
    required=True,
    help="Target grid: config name (e.g., 'gfs_0p25') or path to NetCDF file",
)
@click.option(
    "--region",
    type=str,
    help="Region name for grid extent (e.g., 'europe')",
)
@click.option(
    "--method",
    type=click.Choice(["bilinear", "conservative", "nearest_s2d", "nearest_d2s"]),
    default="bilinear",
    help="Regridding method",
)
@click.option(
    "--output",
    type=click.Path(),
    required=True,
    help="Output NetCDF file path",
)
@click.pass_context
def regrid(
    ctx,
    source: str,
    target_grid: str,
    region: Optional[str],
    method: str,
    output: str,
):
    """Regrid a dataset to a target grid."""
    config = ctx.obj["config"]

    try:
        # Load source dataset
        logger.info(f"Loading source dataset: {source}")
        ds_source = load_dataset(Path(source))

        # Determine target grid
        if Path(target_grid).exists():
            # Load from file
            logger.info(f"Loading target grid from file: {target_grid}")
            ds_target = load_dataset(Path(target_grid))
        else:
            # Create from config
            if not region:
                region = config["defaults"]["region"]

            logger.info(f"Creating target grid: {target_grid} for region: {region}")
            ds_target = get_grid_from_config(config, target_grid, region)

        # Perform regridding
        ds_regridded = regrid_dataset(ds_source, ds_target, method=method)

        # Save output
        output_path = Path(output)
        save_dataset(ds_regridded, output_path)

        click.echo(f"✓ Successfully regridded data to: {output_path}")

    except Exception as e:
        logger.error(f"Regridding failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--var",
    "variable",
    required=True,
    help="Variable name to analyze (must be present in all files)",
)
@click.option(
    "--files",
    required=True,
    multiple=True,
    type=click.Path(exists=True),
    help="Input NetCDF files (must be on same grid). Repeat --files for each file.",
)
@click.option(
    "--labels",
    multiple=True,
    help="Labels for each file (same order as --files). Repeat --labels for each label.",
)
@click.option(
    "--output",
    type=click.Path(),
    required=True,
    help="Output PNG file for spread map",
)
@click.option(
    "--json",
    "json_output",
    type=click.Path(),
    help="Optional JSON file for analysis results",
)
@click.pass_context
def analyze(
    ctx,
    variable: str,
    files: tuple,
    labels: Optional[tuple],
    output: str,
    json_output: Optional[str],
):
    """Analyze and compare multiple datasets."""
    try:
        # Validate inputs
        if len(files) < 2:
            raise ValueError("Need at least 2 files for analysis")

        if labels and len(labels) != len(files):
            raise ValueError(f"Number of labels ({len(labels)}) must match files ({len(files)})")

        # Convert to lists
        file_list = list(files)
        label_list = list(labels) if labels else None

        # Load datasets
        logger.info(f"Loading {len(file_list)} datasets")
        datasets = []
        for file_path in file_list:
            ds = load_dataset(Path(file_path))
            datasets.append(ds)

        # Perform analysis
        results = analyze_datasets(
            datasets,
            variable,
            labels=label_list,
            output_map=Path(output),
        )

        # Print summary
        print_analysis_summary(results)

        # Export JSON if requested
        if json_output:
            export_analysis_json(results, Path(json_output))
            click.echo(f"✓ Analysis results saved to: {json_output}")

        click.echo(f"✓ Spread map saved to: {output}")

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def info(ctx):
    """Display configuration information."""
    config = ctx.obj["config"]

    click.echo("\n" + "=" * 70)
    click.echo("WeatherDataTool Configuration")
    click.echo("=" * 70)

    # Providers
    click.echo("\n--- Available Providers ---")
    for name, provider_config in config["providers"].items():
        enabled = provider_config.get("enabled", True)
        status = "✓" if enabled else "✗"
        click.echo(f"  {status} {name}: {provider_config['name']}")

    # Regions
    click.echo("\n--- Available Regions ---")
    for name, region_config in config["regions"].items():
        click.echo(
            f"  • {name}: "
            f"lat=[{region_config['lat_min']}, {region_config['lat_max']}], "
            f"lon=[{region_config['lon_min']}, {region_config['lon_max']}]"
        )

    # Reference grids
    click.echo("\n--- Reference Grids ---")
    for name, grid_config in config["reference_grids"].items():
        click.echo(f"  • {name}: {grid_config['resolution']}° - {grid_config['description']}")

    click.echo("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    cli()
