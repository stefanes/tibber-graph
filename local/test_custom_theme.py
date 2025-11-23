"""Test custom theme validation and functionality."""
import sys
from pathlib import Path

# Add parent directory to path to import from custom_components
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "tibber_graph"))

from themes import validate_custom_theme, get_theme_config, REQUIRED_THEME_FIELDS


def test_validate_custom_theme_valid():
    """Test validation with a valid custom theme."""
    valid_theme = {
        "avgline_color": "#eab308",
        "avgline_style": ":",
        "axis_label_color": "#cfd6e6",
        "background_color": "#1c1c1c",
        "cheap_price_color": "#2d5a3d",
        "cheapline_color": "#34d399",
        "cheapline_style": ":",
        "fill_alpha": 0.18,
        "fill_color": "#7dc3ff",
        "grid_alpha": 0.45,
        "grid_color": "#2a2f36",
        "label_color": "#e6edf3",
        "label_color_avg": "#eab308",
        "label_color_max": "#fb7185",
        "label_color_min": "#34d399",
        "label_stroke": True,
        "nowline_alpha": 0.5,
        "nowline_color": "#ff6b6b",
        "plot_linewidth": 1.0,
        "price_line_color": "#7dc3ff",
        "price_line_color_above_avg": "#fb7185",
        "price_line_color_below_avg": "#7dc3ff",
        "price_line_color_near_avg": "#eab308",
        "spine_color": "#3a4250",
        "tick_color": "#cfd6e6",
        "tickline_color": "#1f2530"
    }

    is_valid, error = validate_custom_theme(valid_theme)
    assert is_valid, f"Expected valid theme, got error: {error}"
    print("✓ Valid theme test passed")


def test_validate_custom_theme_missing_fields():
    """Test validation with missing required fields."""
    incomplete_theme = {
        "axis_label_color": "#cfd6e6",
        "background_color": "#1c1c1c",
        # Partial themes are allowed; missing keys are filled from built-in theme
    }

    is_valid, error = validate_custom_theme(incomplete_theme)
    assert is_valid, f"Expected partial theme to be accepted, got error: {error}"
    print("✓ Partial theme acceptance test passed")


def test_validate_custom_theme_not_dict():
    """Test validation with non-dictionary input."""
    is_valid, error = validate_custom_theme("not a dict")
    assert not is_valid, "Expected invalid for non-dict input"
    assert "must be a dictionary" in error, f"Expected dict error, got: {error}"
    print(f"✓ Non-dict test passed: {error}")


def test_get_theme_config_custom_priority():
    """Test that custom theme takes priority over named theme."""
    custom_theme = {
        "avgline_color": "#custom",
        "avgline_style": ":",
        "axis_label_color": "#custom",
        "background_color": "#custom",
        "cheap_price_color": "#custom",
        "cheapline_color": "#custom",
        "cheapline_style": ":",
        "fill_alpha": 0.99,
        "fill_color": "#custom",
        "grid_alpha": 0.99,
        "grid_color": "#custom",
        "label_color": "#custom",
        "label_color_avg": "#custom",
        "label_color_max": "#custom",
        "label_color_min": "#custom",
        "label_stroke": False,
        "nowline_alpha": 0.99,
        "nowline_color": "#custom",
        "plot_linewidth": 9.9,
        "price_line_color": "#custom",
        "price_line_color_above_avg": "#custom",
        "price_line_color_below_avg": "#custom",
        "price_line_color_near_avg": "#custom",
        "spine_color": "#custom",
        "tick_color": "#custom",
        "tickline_color": "#custom"
    }

    # Test custom theme takes priority
    result = get_theme_config("dark", custom_theme)
    assert result["background_color"] == "#custom", "Expected custom theme to be used"
    assert result["fill_alpha"] == 0.99, "Expected custom values"
    print("✓ Custom theme priority test passed")


def test_get_theme_config_named_theme():
    """Test that named themes work when no custom theme is provided."""
    # Test dark theme
    dark_config = get_theme_config("dark", None)
    assert "background_color" in dark_config, "Expected background_color in theme"
    assert dark_config["background_color"] == "#1c1c1c", f"Expected dark background, got {dark_config['background_color']}"
    print("✓ Named theme test passed (dark)")

    # Test light theme
    light_config = get_theme_config("light", None)
    assert light_config["background_color"] == "#ffffff", f"Expected light background, got {light_config['background_color']}"
    print("✓ Named theme test passed (light)")


def test_required_fields_count():
    """Test that REQUIRED_THEME_FIELDS has the expected number of fields."""
    expected_count = 26  # Added avgline_style and cheapline_style
    actual_count = len(REQUIRED_THEME_FIELDS)
    assert actual_count == expected_count, f"Expected {expected_count} required fields, got {actual_count}"
    print(f"✓ Required fields count test passed ({actual_count} fields)")


if __name__ == "__main__":
    print("Running custom theme tests...\n")

    try:
        test_validate_custom_theme_valid()
        test_validate_custom_theme_missing_fields()
        test_validate_custom_theme_not_dict()
        test_get_theme_config_custom_priority()
        test_get_theme_config_named_theme()
        test_required_fields_count()

        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
