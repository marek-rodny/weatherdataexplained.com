#!/bin/bash
# Quick analysis of existing regridded data

set -e

echo "========================================="
echo "WeatherDataTool - Quick Analysis"
echo "========================================="
echo ""

# Check if processed data exists
PROCESSED_DIR="data/processed"

if [ ! -d "$PROCESSED_DIR" ] || [ -z "$(ls -A $PROCESSED_DIR)" ]; then
    echo "ERROR: No processed data found in $PROCESSED_DIR"
    echo ""
    echo "Please run the full pipeline first:"
    echo "  ./scripts/run_pipeline.sh"
    echo ""
    echo "Or download and regrid data manually:"
    echo "  python -m weather_data_tool.cli download --help"
    echo "  python -m weather_data_tool.cli regrid --help"
    exit 1
fi

echo "Available processed files:"
ls -lh "$PROCESSED_DIR"
echo ""

# Get list of NetCDF files
FILES=($PROCESSED_DIR/*.nc)

if [ ${#FILES[@]} -eq 0 ]; then
    echo "ERROR: No NetCDF files found in $PROCESSED_DIR"
    exit 1
fi

# If only one file, duplicate it for analysis (just for demo)
if [ ${#FILES[@]} -eq 1 ]; then
    echo "Note: Only one file found. For true ensemble analysis, add more models."
    echo "Creating simple visualization..."
    echo ""

    # Extract variable name from filename (assumes format: provider_var_f*.nc)
    FILENAME=$(basename "${FILES[0]}")
    VAR=$(echo "$FILENAME" | cut -d'_' -f2)

    python -m weather_data_tool.cli analyze \
        --var "$VAR" \
        --files "${FILES[0]}" \
        --files "${FILES[0]}" \
        --labels "Model-A" "Model-B" \
        --output "outputs/quick_analysis.png" \
        --json "outputs/quick_analysis.json"

else
    echo "Found ${#FILES[@]} files. Creating ensemble analysis..."
    echo ""

    # Extract variable name from first file
    FILENAME=$(basename "${FILES[0]}")
    VAR=$(echo "$FILENAME" | cut -d'_' -f2)

    # Build file arguments
    FILE_ARGS=""
    LABEL_ARGS=""
    for i in "${!FILES[@]}"; do
        FILE_ARGS="$FILE_ARGS --files ${FILES[$i]}"

        # Generate label from filename
        LABEL=$(basename "${FILES[$i]}" .nc | cut -d'_' -f1)
        LABEL_ARGS="$LABEL_ARGS --labels $LABEL"
    done

    # Run analysis
    python -m weather_data_tool.cli analyze \
        --var "$VAR" \
        $FILE_ARGS \
        $LABEL_ARGS \
        --output "outputs/ensemble_analysis.png" \
        --json "outputs/ensemble_analysis.json"
fi

echo ""
echo "========================================="
echo "Analysis Complete!"
echo "========================================="
echo ""
echo "Output files:"
echo "  - outputs/*.png (maps)"
echo "  - outputs/*.json (statistics)"
echo ""
