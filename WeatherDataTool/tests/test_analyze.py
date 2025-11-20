"""Tests for analyze module."""

import json

import numpy as np
import pytest

from weather_data_tool.analyze import (
    analyze_datasets,
    compute_ensemble_spread,
    compute_pairwise_differences,
    create_spread_map,
    export_analysis_json,
    find_top_spread_locations,
)


def test_compute_ensemble_spread(sample_datasets_ensemble):
    """Test ensemble spread computation."""
    mean, std, stacked = compute_ensemble_spread(
        sample_datasets_ensemble,
        "t2m",
    )

    # Check shapes
    assert mean.shape == sample_datasets_ensemble[0]["t2m"].shape
    assert std.shape == sample_datasets_ensemble[0]["t2m"].shape

    # Check that std is non-negative
    assert (std >= 0).all()

    # Check that stacked has model dimension
    assert "model" in stacked.dims
    assert stacked.sizes["model"] == len(sample_datasets_ensemble)


def test_compute_ensemble_spread_single_dataset(sample_datasets_ensemble):
    """Test error handling with single dataset."""
    with pytest.raises(ValueError, match="at least 2 datasets"):
        compute_ensemble_spread([sample_datasets_ensemble[0]], "t2m")


def test_compute_ensemble_spread_missing_variable(sample_datasets_ensemble):
    """Test error handling with missing variable."""
    with pytest.raises(ValueError, match="not found"):
        compute_ensemble_spread(sample_datasets_ensemble, "nonexistent_var")


def test_compute_pairwise_differences(sample_datasets_ensemble):
    """Test pairwise difference computation."""
    labels = ["Model_A", "Model_B", "Model_C"]
    differences = compute_pairwise_differences(
        sample_datasets_ensemble,
        "t2m",
        labels=labels,
    )

    # Check that we have the right number of pairs
    n_datasets = len(sample_datasets_ensemble)
    n_pairs = n_datasets * (n_datasets - 1) // 2
    assert len(differences) == n_pairs

    # Check keys
    assert "Model_A_minus_Model_B" in differences

    # Check shapes
    for diff in differences.values():
        assert diff.shape == sample_datasets_ensemble[0]["t2m"].shape


def test_compute_pairwise_differences_no_labels(sample_datasets_ensemble):
    """Test pairwise differences without labels."""
    differences = compute_pairwise_differences(
        sample_datasets_ensemble,
        "t2m",
    )

    # Should generate default labels
    assert "Model_0_minus_Model_1" in differences


def test_find_top_spread_locations(sample_datasets_ensemble):
    """Test finding top spread locations."""
    _, spread, _ = compute_ensemble_spread(sample_datasets_ensemble, "t2m")

    locations = find_top_spread_locations(spread, top_n=3)

    assert len(locations) == 3

    # Check structure
    for loc in locations:
        assert "lat" in loc
        assert "lon" in loc
        assert "spread" in loc

    # Check that spreads are in descending order
    spreads = [loc["spread"] for loc in locations]
    assert spreads == sorted(spreads, reverse=True)


def test_create_spread_map(sample_datasets_ensemble, tmp_output_dir):
    """Test creating spread map visualization."""
    _, spread, _ = compute_ensemble_spread(sample_datasets_ensemble, "t2m")

    output_file = tmp_output_dir / "spread_map.png"

    create_spread_map(
        spread,
        output_file,
        title="Test Spread Map",
        variable_name="t2m",
        units="K",
    )

    # Check that file was created
    assert output_file.exists()

    # Check file size is reasonable (should be a valid PNG)
    assert output_file.stat().st_size > 1000  # At least 1KB


def test_analyze_datasets(sample_datasets_ensemble, tmp_output_dir):
    """Test full analysis pipeline."""
    labels = ["GFS", "GEFS", "ICON"]
    output_map = tmp_output_dir / "analysis_map.png"

    results = analyze_datasets(
        sample_datasets_ensemble,
        "t2m",
        labels=labels,
        output_map=output_map,
    )

    # Check results structure
    assert "variable" in results
    assert "n_models" in results
    assert "spread_statistics" in results
    assert "top_spread_locations" in results
    assert "model_statistics" in results

    # Check values
    assert results["variable"] == "t2m"
    assert results["n_models"] == 3

    # Check spread statistics
    spread_stats = results["spread_statistics"]
    assert "mean_spread" in spread_stats
    assert "max_spread" in spread_stats
    assert "min_spread" in spread_stats
    assert spread_stats["mean_spread"] > 0

    # Check top locations
    assert len(results["top_spread_locations"]) == 3

    # Check model statistics
    assert len(results["model_statistics"]) == 3
    for stat in results["model_statistics"]:
        assert "label" in stat
        assert "mean" in stat
        assert "std" in stat

    # Check that map was created
    assert output_map.exists()


def test_analyze_datasets_no_map(sample_datasets_ensemble):
    """Test analysis without creating map."""
    results = analyze_datasets(
        sample_datasets_ensemble,
        "t2m",
        labels=["A", "B", "C"],
        output_map=None,
    )

    assert "variable" in results
    assert results["n_models"] == 3


def test_export_analysis_json(sample_datasets_ensemble, tmp_output_dir):
    """Test exporting analysis results to JSON."""
    results = analyze_datasets(
        sample_datasets_ensemble,
        "t2m",
        labels=["GFS", "GEFS", "ICON"],
    )

    json_file = tmp_output_dir / "results.json"
    export_analysis_json(results, json_file)

    # Check file exists
    assert json_file.exists()

    # Load and validate JSON
    with open(json_file, "r") as f:
        loaded_results = json.load(f)

    assert loaded_results["variable"] == "t2m"
    assert loaded_results["n_models"] == 3
    assert "spread_statistics" in loaded_results
