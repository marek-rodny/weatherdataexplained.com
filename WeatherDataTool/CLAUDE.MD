# WeatherDataTool Developer Guide

## Purpose

WeatherDataTool is a production-quality Python package for downloading, preprocessing, regridding, and analyzing open weather forecast data. The tool prioritizes **xarray-friendly sources** (NetCDF/OPeNDAP/Zarr) to avoid GRIB parsing complexity and enable lazy loading of large datasets.

### Key Design Goals

1. **Avoid GRIB complexity**: Use NetCDF/OPeNDAP/Zarr sources wherever possible
2. **Lazy loading**: Leverage xarray's lazy evaluation for memory efficiency
3. **Reproducibility**: All operations are configurable and deterministic
4. **Production-ready**: Comprehensive tests, logging, error handling, and CI/CD
5. **Extensibility**: Easy to add new providers and analysis methods

## Architecture

### Project Structure

```
WeatherDataTool/
├── src/weather_data_tool/
│   ├── __init__.py           # Package exports
│   ├── cli.py                # Command-line interface (Click)
│   ├── download.py           # Provider classes for data access
│   ├── regrid.py             # Regridding with xESMF
│   ├── io.py                 # I/O utilities (save/load/subset)
│   ├── utils.py              # Utilities (config, logging, validation)
│   └── analyze.py            # Analysis and visualization
├── configs/
│   └── config.yaml           # Configuration (providers, regions, grids)
├── tests/                    # Pytest test suite
│   ├── conftest.py           # Fixtures
│   └── test_*.py             # Test modules
├── scripts/                  # Shell scripts for common workflows
├── data/                     # Data directories (gitignored)
│   ├── raw/                  # Downloaded data
│   └── processed/            # Regridded data
└── outputs/                  # Analysis outputs (maps, JSON)
```

### Core Modules

#### `download.py` - Data Providers

**Provider Protocol**: All providers implement a common interface:

```python
class Provider(Protocol):
    name: str
    def open_dataset(
        self,
        variable: str,
        forecast_hour: int,
        run_time: Optional[datetime]
    ) -> xr.Dataset:
        ...
```

**Base Provider**: `BaseProvider` abstract class provides:
- Configuration management
- Variable name mapping (standard → provider-specific)
- Forecast hour validation
- Latest run time detection

**Concrete Providers**:
1. **GFSOpenDAPProvider**: Accesses NOAA GFS via NOMADS OPeNDAP
   - URL pattern: `https://nomads.ncep.noaa.gov/dods/gfs_0p25/gfs{date}/gfs_0p25_{cycle}z`
   - Variables: t2m, u10, v10, msl, tp (precip)
   - Stability: Good for recent runs (last 2-3 days)

2. **HRRRZarrProvider**: Accesses HRRR via cloud-optimized Zarr (AWS)
   - URL pattern: `s3://hrrrzarr/sfc/{date}/{date}_{cycle}z_anl.zarr`
   - CONUS only, high resolution (~3km)
   - Requires fsspec with s3 support

#### `regrid.py` - Regridding

Uses **xESMF** (xarray-ESMFpy) for conservative and bilinear regridding.

**Key Functions**:
- `create_reference_grid()`: Construct regular lat-lon grid
- `get_grid_from_config()`: Create grid from config (resolution + region)
- `regrid_dataset()`: Regrid with caching of regridding weights
- `prepare_dataset_for_regridding()`: Normalize coordinate names

**Methods supported**: bilinear, conservative, nearest_s2d, nearest_d2s

**Weight caching**: xESMF caches regridding weights to speed up repeated operations with the same source/target grids.

#### `io.py` - I/O Utilities

- `infer_coord_names()`: Handle different coordinate naming (lat/latitude, lon/longitude)
- `normalize_longitude()`: Convert [0, 360] → [-180, 180]
- `spatial_subset()`: Extract region using lat/lon bounds
- `save_dataset()`: Write NetCDF with compression
- `load_dataset()`: Load NetCDF with xarray
- `get_variable_metadata()`: Extract CF metadata

#### `analyze.py` - Analysis & Visualization

**Ensemble Analysis**:
- `compute_ensemble_spread()`: Calculate mean and std dev across models
- `compute_pairwise_differences()`: All pairwise model differences
- `find_top_spread_locations()`: Identify high-uncertainty areas

**Visualization**:
- `create_spread_map()`: Generate PNG map of ensemble spread
- Uses Cartopy if available (falls back to basic matplotlib)
- Automatically adds coastlines, borders, gridlines

**Output**:
- PNG maps with colorbars and titles
- JSON summaries with statistics and top locations

#### `cli.py` - Command-Line Interface

Built with **Click**. Commands:
- `download`: Fetch data from provider
- `regrid`: Regrid to target grid
- `analyze`: Compare forecasts and generate maps
- `info`: Display configuration

All commands use context to pass configuration and support `--log-level` for debugging.

## Data Sources

### NOAA GFS via NOMADS OPeNDAP

**Pros**:
- Direct xarray access (no GRIB parsing)
- Global coverage, 0.25° resolution
- Recent runs readily available

**Cons**:
- Only recent forecasts (rolling window)
- Can be slow or unavailable during maintenance
- Limited historical data

**Alternative**: AWS Open Data (GRIB2, requires cfgrib - not implemented to avoid GRIB dependency)

### HRRR via Zarr (Herbie/AWS)

**Pros**:
- Cloud-optimized, fast access
- High resolution (~3km)
- Good for CONUS applications

**Cons**:
- CONUS only
- Zarr endpoints can change
- May require AWS credentials for some operations

**Note**: Actual Herbie integration would require the `herbie-data` package for automatic Zarr path discovery.

## Configuration

### `configs/config.yaml`

**Regions**: Define spatial domains
```yaml
regions:
  europe:
    lat_min: 30
    lat_max: 72
    lon_min: -25
    lon_max: 45
```

**Reference Grids**: Define target resolutions
```yaml
reference_grids:
  gfs_0p25:
    resolution: 0.25
    description: "GFS 0.25 degree grid"
```

**Providers**: Configure data sources
```yaml
providers:
  gfs_opendap:
    name: "NOAA GFS via NOMADS OPeNDAP"
    type: opendap
    base_url: "https://nomads.ncep.noaa.gov/dods/..."
    variables:
      t2m: "tmp2m"  # standard: provider-specific
    forecast_hours: [0, 6, 12, 24, 48, 72]
    enabled: true
```

## Adding New Providers

1. **Create Provider Class** in `download.py`:

```python
class NewProvider(BaseProvider):
    def open_dataset(
        self,
        variable: str,
        forecast_hour: int,
        run_time: Optional[datetime] = None
    ) -> xr.Dataset:
        # Build URL from self.base_url, run_time, etc.
        url = self.base_url.format(...)

        # Open with xarray (OPeNDAP or Zarr)
        ds = xr.open_dataset(url)  # or xr.open_zarr(...)

        # Select variable and time
        provider_var = self.get_variable_name(variable)
        ds = ds[[provider_var]]

        # Rename to standard name
        ds = ds.rename({provider_var: variable})

        return ds
```

2. **Register in Factory** (`get_provider()` function):

```python
provider_classes = {
    "opendap": GFSOpenDAPProvider,
    "zarr": HRRRZarrProvider,
    "new_type": NewProvider,  # Add here
}
```

3. **Add to Config** (`configs/config.yaml`):

```yaml
providers:
  new_provider:
    name: "My New Provider"
    type: new_type
    base_url: "https://..."
    variables:
      t2m: "provider_temp_name"
```

4. **Test**: Create synthetic tests in `tests/test_download.py`

## Testing

### Philosophy

- **No network calls in tests**: Use synthetic xarray datasets
- **Fast execution**: Full suite should run in <60s
- **Comprehensive coverage**: Test all modules and edge cases

### Fixtures (`tests/conftest.py`)

- `sample_config`: Configuration dictionary
- `sample_dataset_small`: 10x10 grid for fast tests
- `sample_dataset_medium`: 20x30 grid with multiple variables
- `sample_datasets_ensemble`: 3 ensemble members for spread tests
- `reference_grid_*`: Target grids for regridding tests

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_regrid.py

# With coverage
pytest --cov=weather_data_tool --cov-report=html

# Verbose
pytest -v

# Stop on first failure
pytest -x
```

### Test Coverage

Current coverage targets:
- **Core modules**: >90%
- **CLI**: >80% (some Click internals hard to test)
- **Overall**: >85%

## CI/CD

### GitHub Actions (`.github/workflows/ci.yml`)

**Workflow**:
1. Checkout code
2. Set up Python 3.11
3. Install system dependencies (GEOS, PROJ for cartopy)
4. Install Python dependencies
5. Run pytest
6. (Optional) Upload coverage reports

**Triggers**:
- Push to `main` branch
- Pull requests
- Manual workflow dispatch

**Testing Strategy**:
- Matrix testing across Python 3.9, 3.10, 3.11
- Test with/without optional dependencies (cartopy)

## Git Workflow

### Initial Repository Setup

```bash
# Initialize repo
cd WeatherDataTool
git init
git add .
git commit -m "feat: initial WeatherDataTool with providers, regridding, analysis, tests, CI"

# Add remote and push
git branch -M main
git remote add origin <YOUR_REPO_URL>
git push -u origin main
```

### Feature Branch Workflow

```bash
# Create feature branch
git checkout -b feature/add-ecmwf-provider

# Make changes, add tests
# ...

# Commit changes
git add .
git commit -m "feat: add ECMWF provider with OPeNDAP support"

# Push branch
git push -u origin feature/add-ecmwf-provider

# Create Pull Request on GitHub
# After review and CI passes, merge to main
```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Examples:
```
feat: add ICON model provider
fix: handle missing coordinates in regridding
docs: update README with installation instructions
test: add edge case tests for spatial subsetting
```

## Common Development Tasks

### Add New Variable

1. Add to provider config (`configs/config.yaml`):
```yaml
providers:
  gfs_opendap:
    variables:
      mslp: "msletmsl"  # Add new variable mapping
```

2. Update tests if needed

3. Document in README

### Add New Region

```yaml
regions:
  my_region:
    lat_min: 10
    lat_max: 40
    lon_min: 50
    lon_max: 120
```

### Change Default Grid Resolution

```yaml
reference_grids:
  custom_grid:
    resolution: 0.5  # Change resolution
    description: "Custom 0.5 degree grid"

defaults:
  reference_grid: custom_grid  # Set as default
```

## Performance Optimization

### Memory

- Use spatial subsetting to reduce data size
- Process one variable at a time
- Close datasets when done: `ds.close()`
- Use Dask for parallel processing (optional)

### Speed

- Regridding weights are cached by xESMF
- Use coarser target grids when high resolution isn't needed
- Download only required forecast hours
- Use OPeNDAP's built-in subsetting when possible

## Future Improvements

### Short-term
1. **Add more providers**: ECMWF, ICON, UKMO
2. **Caching layer**: Local filesystem cache with ETag/timestamp checks
3. **Parallel downloads**: Download multiple variables/times concurrently
4. **Makefile**: `make test`, `make fmt`, `make docs`
5. **Better error messages**: Provider-specific troubleshooting hints

### Medium-term
1. **Time series analysis**: Track forecast evolution over time
2. **Skill scores**: RMSE, bias, correlation against observations
3. **Ensemble statistics**: Beyond spread (percentiles, probability maps)
4. **Interactive maps**: Plotly or Bokeh for web visualization
5. **API server**: Flask/FastAPI wrapper for web services

### Long-term
1. **AI summaries**: LLM-generated forecast summaries from spreads
2. **Anomaly detection**: Flag unusual forecast patterns
3. **Multi-model workflows**: Automated ensemble processing pipelines
4. **Cloud deployment**: Docker containers, Kubernetes orchestration
5. **Real-time monitoring**: Webhook notifications for high spreads

## Troubleshooting

### Common Issues

**1. Cartopy installation fails**

```bash
# Install system dependencies first
sudo apt-get install libgeos-dev libproj-dev  # Ubuntu/Debian
brew install geos proj  # macOS
```

**2. xESMF regridding is slow**

- First run generates weights (can take 1-2 minutes)
- Subsequent runs reuse cached weights (seconds)
- Check `~/.esmf` for weight files

**3. Provider returns no data**

- Recent run may not be available yet (wait 2-3 hours after run time)
- NOMADS can be down for maintenance
- Try a different run time with `--run-time`

**4. Out of memory**

- Reduce region size with `--bounds`
- Use coarser grid resolution
- Process variables separately

**5. Tests fail with import errors**

- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check Python version >= 3.9

## License

MIT License

Copyright (c) 2024 WeatherDataTool Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contact

- **Issues**: GitHub Issues
- **Contributions**: Pull Requests welcome
- **Questions**: Open a GitHub Discussion

## References

- [xarray documentation](https://docs.xarray.dev/)
- [xESMF documentation](https://xesmf.readthedocs.io/)
- [NOAA NOMADS](https://nomads.ncep.noaa.gov/)
- [Cartopy documentation](https://scitools.org.uk/cartopy/)
- [CF Conventions](http://cfconventions.org/)
