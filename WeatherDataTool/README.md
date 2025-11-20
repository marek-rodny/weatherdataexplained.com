# WeatherDataTool

A production-quality Python tool for downloading, regridding, and analyzing weather forecast data from xarray-friendly sources (NetCDF/OPeNDAP/Zarr).

## Features

- **Download** weather forecast data from multiple providers (NOAA GFS, HRRR)
- **Regrid** datasets to common grids using xESMF
- **Analyze** ensemble spread and compare multiple forecasts
- **Visualize** results with automated map generation
- **CLI** for easy automation and scripting
- **Production-ready** with comprehensive tests and CI/CD

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd WeatherDataTool

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Basic Usage

#### 1. Download Data

Download GFS 2m temperature forecast for Europe at +24 hours:

```bash
python -m weather_data_tool.cli download \
    --provider gfs_opendap \
    --variable t2m \
    --forecast-hour 24 \
    --region europe \
    --output data/raw/gfs_t2m_f024.nc
```

#### 2. Regrid to Common Grid

Regrid the downloaded data to a 0.25° grid:

```bash
python -m weather_data_tool.cli regrid \
    --source data/raw/gfs_t2m_f024.nc \
    --target-grid gfs_0p25 \
    --region europe \
    --output data/processed/gfs_t2m_f024_regridded.nc
```

#### 3. Analyze Multiple Forecasts

Compare forecasts and visualize ensemble spread:

```bash
python -m weather_data_tool.cli analyze \
    --var t2m \
    --files data/processed/gfs_t2m_f024_regridded.nc \
    --files data/processed/gefs_t2m_f024_regridded.nc \
    --labels GFS GEFS \
    --output outputs/t2m_spread_map.png \
    --json outputs/analysis_results.json
```

### Using the Shell Scripts

Quick analysis pipeline:

```bash
# Run full pipeline
./scripts/run_pipeline.sh

# Quick single-forecast analysis
./scripts/quick_analyze.sh
```

## Data Providers

### GFS via OPeNDAP (NOMADS)
- **Source**: NOAA NOMADS OPeNDAP
- **Resolution**: 0.25°
- **Coverage**: Global
- **Variables**: t2m, u10, v10, msl, tp
- **Availability**: Recent runs (last few days)

### HRRR via Zarr
- **Source**: AWS cloud-optimized Zarr
- **Resolution**: ~3km
- **Coverage**: CONUS only
- **Variables**: t2m, u10, v10, tp
- **Availability**: Depends on AWS Open Data availability

## Configuration

Edit `configs/config.yaml` to:
- Add new regions
- Configure reference grids
- Add or modify data providers
- Change default settings

Example region definition:

```yaml
regions:
  europe:
    lat_min: 30
    lat_max: 72
    lon_min: -25
    lon_max: 45
```

## CLI Commands

### `download`
Download weather data from a provider.

**Options:**
- `--provider`: Data provider name (e.g., 'gfs_opendap')
- `--variable`: Variable name (e.g., 't2m', 'u10')
- `--forecast-hour`: Forecast hour (e.g., 24)
- `--run-time`: Optional ISO datetime for specific model run
- `--region`: Region name from config
- `--bounds`: Custom bounds as 'lat_min,lat_max,lon_min,lon_max'
- `--output`: Output file path

### `regrid`
Regrid dataset to target grid.

**Options:**
- `--source`: Source NetCDF file
- `--target-grid`: Grid name or path to template file
- `--region`: Region for grid extent
- `--method`: Regridding method (bilinear, conservative, nearest_s2d, nearest_d2s)
- `--output`: Output file path

### `analyze`
Analyze and compare multiple datasets.

**Options:**
- `--var`: Variable name
- `--files`: Input files (repeat for each file)
- `--labels`: Labels for files (repeat for each label)
- `--output`: Output PNG file for map
- `--json`: Optional JSON output for results

### `info`
Display configuration information.

```bash
python -m weather_data_tool.cli info
```

## Python API

```python
from weather_data_tool import (
    get_provider,
    regrid_dataset,
    analyze_datasets,
    save_dataset,
)
from weather_data_tool.utils import load_config

# Load configuration
config = load_config()

# Get provider and download data
provider = get_provider("gfs_opendap", config)
ds = provider.open_dataset("t2m", forecast_hour=24)

# Regrid
from weather_data_tool.regrid import get_grid_from_config
target_grid = get_grid_from_config(config, "gfs_0p25", "europe")
ds_regridded = regrid_dataset(ds, target_grid)

# Analyze
results = analyze_datasets(
    [ds1_regridded, ds2_regridded],
    variable="t2m",
    labels=["GFS", "GEFS"],
    output_map="spread_map.png"
)
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=weather_data_tool --cov-report=html

# Run specific test file
pytest tests/test_regrid.py

# Run specific test
pytest tests/test_regrid.py::test_regrid_dataset
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/
```

## Troubleshooting

### Cartopy Installation Issues

If cartopy fails to install:

```bash
# On Ubuntu/Debian
sudo apt-get install libgeos-dev libproj-dev

# On macOS
brew install geos proj

# Then retry
pip install cartopy
```

The tool will work without cartopy, but maps will use basic matplotlib plotting.

### xESMF First Run

The first regridding operation may take longer as xESMF generates and caches regridding weights. Subsequent operations with the same grids will be much faster.

### Data Provider Issues

If a provider fails:
- Check that the forecast run is available (recent runs only for NOMADS)
- Verify network connectivity
- Try a different run time: `--run-time "2024-01-15T12:00:00"`
- Check provider status in `configs/config.yaml`

### Memory Issues

For large datasets:
- Use smaller regions: `--bounds "40,50,-10,10"`
- Reduce grid resolution in `configs/config.yaml`
- Process variables separately

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run tests: `pytest`
5. Commit: `git commit -m "feat: add my feature"`
6. Push: `git push origin feature/my-feature`
7. Create a Pull Request

## License

MIT License - see LICENSE file for details.

## Citation

If you use WeatherDataTool in your research, please cite:

```
WeatherDataTool: Production-quality weather forecast data processing
https://github.com/yourusername/WeatherDataTool
```

## Links

- **Documentation**: See CLAUDE.MD for detailed developer guide
- **Issues**: Report bugs and request features on GitHub Issues
- **Data Sources**:
  - [NOAA NOMADS](https://nomads.ncep.noaa.gov/)
  - [AWS Open Data](https://registry.opendata.aws/noaa-hrrr-pds/)

## Acknowledgments

- NOAA for providing open weather data
- xarray, xESMF, and related Python scientific stack
- Cartopy for mapping capabilities
