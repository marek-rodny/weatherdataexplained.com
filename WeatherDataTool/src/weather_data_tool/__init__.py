"""
WeatherDataTool: Production-quality weather forecast data processing.

A tool for downloading, regridding, and analyzing weather forecast data
from xarray-friendly sources (NetCDF/OPeNDAP/Zarr).
"""

__version__ = "0.1.0"
__author__ = "WeatherDataTool Contributors"

from weather_data_tool.download import get_provider
from weather_data_tool.regrid import regrid_dataset, create_reference_grid
from weather_data_tool.analyze import compute_ensemble_spread, create_spread_map
from weather_data_tool.io import save_dataset, load_dataset, spatial_subset

__all__ = [
    "get_provider",
    "regrid_dataset",
    "create_reference_grid",
    "compute_ensemble_spread",
    "create_spread_map",
    "save_dataset",
    "load_dataset",
    "spatial_subset",
]
