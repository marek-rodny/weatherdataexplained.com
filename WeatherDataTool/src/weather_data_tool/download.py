"""Data providers for downloading weather forecast data."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Protocol

import fsspec
import xarray as xr

from weather_data_tool.utils import format_run_time, get_cycle_hour

logger = logging.getLogger(__name__)


class Provider(Protocol):
    """Protocol defining the interface for data providers."""

    name: str

    def open_dataset(
        self,
        variable: str,
        forecast_hour: int,
        run_time: Optional[datetime] = None,
    ) -> xr.Dataset:
        """
        Open a remote dataset for a specific variable and forecast hour.

        Args:
            variable: Variable name (e.g., 't2m', 'u10')
            forecast_hour: Forecast hour
            run_time: Model run time (if None, uses most recent)

        Returns:
            xarray Dataset
        """
        ...


class BaseProvider(ABC):
    """Base class for data providers."""

    def __init__(self, config: Dict):
        """
        Initialize provider with configuration.

        Args:
            config: Provider configuration dictionary
        """
        self.name = config.get("name", "Unknown")
        self.provider_type = config.get("type", "unknown")
        self.base_url = config.get("base_url", "")
        self.variables = config.get("variables", {})
        self.forecast_hours = config.get("forecast_hours", [])
        self.cycles = config.get("cycles", ["00", "06", "12", "18"])
        self.enabled = config.get("enabled", True)

        logger.info(f"Initialized provider: {self.name}")

    def get_variable_name(self, standard_name: str) -> str:
        """
        Get provider-specific variable name from standard name.

        Args:
            standard_name: Standard variable name (e.g., 't2m')

        Returns:
            Provider-specific variable name
        """
        if standard_name not in self.variables:
            raise ValueError(
                f"Variable {standard_name} not available. "
                f"Available: {list(self.variables.keys())}"
            )

        return self.variables[standard_name]

    def validate_forecast_hour(self, forecast_hour: int) -> None:
        """
        Validate forecast hour is available.

        Args:
            forecast_hour: Forecast hour to validate

        Raises:
            ValueError: If forecast hour not available
        """
        if self.forecast_hours and forecast_hour not in self.forecast_hours:
            raise ValueError(
                f"Forecast hour {forecast_hour} not available. "
                f"Available: {self.forecast_hours}"
            )

    def get_latest_run_time(self) -> datetime:
        """
        Get the most recent model run time.

        Returns:
            datetime of latest run
        """
        now = datetime.utcnow()

        # Find most recent cycle
        current_hour = now.hour
        cycle_hours = [int(c) for c in self.cycles]

        # Find the most recent cycle that has likely completed
        for cycle_hour in sorted(cycle_hours, reverse=True):
            if current_hour >= cycle_hour + 3:  # Allow 3 hours for data availability
                run_time = now.replace(hour=cycle_hour, minute=0, second=0, microsecond=0)
                return run_time

        # If no cycle today, use last cycle from yesterday
        yesterday = now - timedelta(days=1)
        latest_cycle = max(cycle_hours)
        run_time = yesterday.replace(hour=latest_cycle, minute=0, second=0, microsecond=0)

        return run_time

    @abstractmethod
    def open_dataset(
        self,
        variable: str,
        forecast_hour: int,
        run_time: Optional[datetime] = None,
    ) -> xr.Dataset:
        """Open remote dataset."""
        pass


class GFSOpenDAPProvider(BaseProvider):
    """NOAA GFS data via NOMADS OPeNDAP."""

    def open_dataset(
        self,
        variable: str,
        forecast_hour: int,
        run_time: Optional[datetime] = None,
    ) -> xr.Dataset:
        """
        Open GFS dataset via OPeNDAP.

        Args:
            variable: Standard variable name (e.g., 't2m')
            forecast_hour: Forecast hour
            run_time: Model run time (if None, uses most recent)

        Returns:
            xarray Dataset with requested variable
        """
        if not self.enabled:
            raise RuntimeError(f"Provider {self.name} is not enabled")

        if run_time is None:
            run_time = self.get_latest_run_time()

        self.validate_forecast_hour(forecast_hour)
        provider_var = self.get_variable_name(variable)

        # Build OPeNDAP URL
        date_str = format_run_time(run_time)
        cycle = get_cycle_hour(run_time)

        # NOMADS OPeNDAP URL format
        url = self.base_url.format(date=date_str, cycle=cycle)

        logger.info(f"Opening GFS data from {url}")
        logger.info(f"Variable: {provider_var}, Forecast hour: {forecast_hour}")

        try:
            # Open with xarray
            ds = xr.open_dataset(url, engine="netcdf4")

            # Select forecast hour
            if "time" in ds.dims:
                ds = ds.isel(time=forecast_hour // 6)  # GFS has 6-hourly output initially

            # Select variable
            if provider_var in ds:
                ds = ds[[provider_var]]
            else:
                available = list(ds.data_vars)[:10]  # Show first 10
                raise ValueError(
                    f"Variable {provider_var} not found. Available: {available}"
                )

            # Rename to standard name
            ds = ds.rename({provider_var: variable})

            logger.info(f"Successfully opened dataset: {dict(ds.sizes)}")
            return ds

        except Exception as e:
            logger.error(f"Failed to open GFS dataset: {e}")
            raise RuntimeError(
                f"Failed to access GFS data. The run may not be available yet. "
                f"Try a different run time or check NOMADS status. Error: {e}"
            )


class HRRRZarrProvider(BaseProvider):
    """HRRR data via cloud-optimized Zarr (Herbie)."""

    def open_dataset(
        self,
        variable: str,
        forecast_hour: int,
        run_time: Optional[datetime] = None,
    ) -> xr.Dataset:
        """
        Open HRRR dataset via Zarr.

        Args:
            variable: Standard variable name (e.g., 't2m')
            forecast_hour: Forecast hour (0-18)
            run_time: Model run time (if None, uses most recent)

        Returns:
            xarray Dataset with requested variable
        """
        if not self.enabled:
            raise RuntimeError(f"Provider {self.name} is not enabled")

        if run_time is None:
            run_time = self.get_latest_run_time()

        self.validate_forecast_hour(forecast_hour)
        provider_var = self.get_variable_name(variable)

        # Build Zarr store URL
        date_str = format_run_time(run_time)
        cycle = get_cycle_hour(run_time)

        url = self.base_url.format(date=date_str, cycle=cycle)

        logger.info(f"Opening HRRR data from {url}")
        logger.info(f"Variable: {provider_var}, Forecast hour: {forecast_hour}")

        try:
            # Open Zarr store
            mapper = fsspec.get_mapper(url, anon=True)
            ds = xr.open_zarr(mapper, consolidated=True)

            # Select forecast hour
            if "time" in ds.dims:
                ds = ds.isel(time=min(forecast_hour, len(ds.time) - 1))

            # Select variable
            if provider_var in ds:
                ds = ds[[provider_var]]
            else:
                available = list(ds.data_vars)[:10]
                raise ValueError(
                    f"Variable {provider_var} not found. Available: {available}"
                )

            # Rename to standard name
            ds = ds.rename({provider_var: variable})

            logger.info(f"Successfully opened dataset: {dict(ds.sizes)}")
            return ds

        except Exception as e:
            logger.error(f"Failed to open HRRR dataset: {e}")
            raise RuntimeError(
                f"Failed to access HRRR data from cloud storage. "
                f"Check AWS credentials or try a different run time. Error: {e}"
            )


def get_provider(provider_name: str, config: Dict) -> BaseProvider:
    """
    Factory function to get a provider instance.

    Args:
        provider_name: Name of provider (e.g., 'gfs_opendap')
        config: Full configuration dictionary

    Returns:
        Provider instance
    """
    providers_config = config.get("providers", {})

    if provider_name not in providers_config:
        available = [k for k, v in providers_config.items() if v.get("enabled", True)]
        raise ValueError(
            f"Provider {provider_name} not found. Available: {available}"
        )

    provider_config = providers_config[provider_name]

    # Map provider types to classes
    provider_classes = {
        "opendap": GFSOpenDAPProvider,
        "zarr": HRRRZarrProvider,
    }

    provider_type = provider_config.get("type", "opendap")

    if provider_type not in provider_classes:
        raise ValueError(f"Unknown provider type: {provider_type}")

    return provider_classes[provider_type](provider_config)
