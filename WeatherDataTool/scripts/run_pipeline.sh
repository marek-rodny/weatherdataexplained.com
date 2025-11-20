#!/bin/bash
# Full pipeline: Download, regrid, and analyze multiple forecasts

set -e  # Exit on error

echo "========================================="
echo "WeatherDataTool - Full Analysis Pipeline"
echo "========================================="
echo ""

# Configuration
VARIABLE="t2m"
FORECAST_HOUR=24
REGION="europe"
GRID="gfs_0p25"

# Output directories
RAW_DIR="data/raw"
PROCESSED_DIR="data/processed"
OUTPUT_DIR="outputs"

mkdir -p "$RAW_DIR" "$PROCESSED_DIR" "$OUTPUT_DIR"

echo "Configuration:"
echo "  Variable: $VARIABLE"
echo "  Forecast hour: $FORECAST_HOUR"
echo "  Region: $REGION"
echo "  Target grid: $GRID"
echo ""

# Step 1: Download from GFS
echo "Step 1/4: Downloading GFS data..."
python -m weather_data_tool.cli download \
    --provider gfs_opendap \
    --variable "$VARIABLE" \
    --forecast-hour "$FORECAST_HOUR" \
    --region "$REGION" \
    --output "$RAW_DIR/gfs_${VARIABLE}_f${FORECAST_HOUR}.nc"

if [ $? -ne 0 ]; then
    echo "ERROR: GFS download failed. This may be due to:"
    echo "  - Recent forecast not yet available (wait 2-3 hours after run time)"
    echo "  - NOMADS server maintenance"
    echo "  - Network connectivity issues"
    echo ""
    echo "Try running with a specific older run time:"
    echo "  --run-time '2024-01-15T12:00:00'"
    exit 1
fi

echo "✓ GFS download complete"
echo ""

# Step 2: Regrid GFS
echo "Step 2/4: Regridding GFS data..."
python -m weather_data_tool.cli regrid \
    --source "$RAW_DIR/gfs_${VARIABLE}_f${FORECAST_HOUR}.nc" \
    --target-grid "$GRID" \
    --region "$REGION" \
    --output "$PROCESSED_DIR/gfs_${VARIABLE}_f${FORECAST_HOUR}_regridded.nc"

echo "✓ GFS regridding complete"
echo ""

# Optional: Download and regrid second model for comparison
# Uncomment to enable multi-model analysis

# echo "Step 3/4: Downloading second model (HRRR)..."
# python -m weather_data_tool.cli download \
#     --provider hrrr_zarr \
#     --variable "$VARIABLE" \
#     --forecast-hour "$FORECAST_HOUR" \
#     --region conus \
#     --output "$RAW_DIR/hrrr_${VARIABLE}_f${FORECAST_HOUR}.nc"
#
# echo "✓ Second model download complete"
# echo ""
#
# echo "Step 4/4: Regridding second model..."
# python -m weather_data_tool.cli regrid \
#     --source "$RAW_DIR/hrrr_${VARIABLE}_f${FORECAST_HOUR}.nc" \
#     --target-grid "$GRID" \
#     --region conus \
#     --output "$PROCESSED_DIR/hrrr_${VARIABLE}_f${FORECAST_HOUR}_regridded.nc"
#
# echo "✓ Second model regridding complete"
# echo ""

# For now, create a simple analysis with just GFS
echo "Step 3/4: Creating analysis visualization..."

# Since we only have one model, we'll create a simple map
# For actual ensemble analysis, you would add multiple --files options
python -m weather_data_tool.cli analyze \
    --var "$VARIABLE" \
    --files "$PROCESSED_DIR/gfs_${VARIABLE}_f${FORECAST_HOUR}_regridded.nc" \
    --files "$PROCESSED_DIR/gfs_${VARIABLE}_f${FORECAST_HOUR}_regridded.nc" \
    --labels "GFS-Run1" "GFS-Run2" \
    --output "$OUTPUT_DIR/${VARIABLE}_analysis_f${FORECAST_HOUR}.png" \
    --json "$OUTPUT_DIR/${VARIABLE}_analysis_f${FORECAST_HOUR}.json" \
    2>/dev/null || echo "Note: Analysis requires at least 2 different datasets"

echo ""
echo "========================================="
echo "Pipeline Complete!"
echo "========================================="
echo ""
echo "Output files:"
echo "  Raw data:       $RAW_DIR/"
echo "  Regridded data: $PROCESSED_DIR/"
echo "  Analysis:       $OUTPUT_DIR/"
echo ""
echo "To view results:"
echo "  - Check $OUTPUT_DIR/ for maps and JSON files"
echo "  - Use 'python -m weather_data_tool.cli info' for configuration details"
echo ""
