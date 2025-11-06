"""Theme loader utility for Tibber Graph integration."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Cache for loaded themes to avoid repeated file reads
_THEMES_CACHE: dict[str, dict[str, Any]] | None = None

# Required theme fields - must all be present in any custom theme
REQUIRED_THEME_FIELDS = {
    "axis_label_color",
    "background_color",
    "cheap_price_color",
    "fill_alpha",
    "fill_color",
    "grid_alpha",
    "grid_color",
    "label_color",
    "label_color_avg",
    "label_color_max",
    "label_color_min",
    "label_stroke",
    "nowline_alpha",
    "nowline_color",
    "plot_linewidth",
    "price_line_color",
    "price_line_color_above_avg",
    "price_line_color_below_avg",
    "price_line_color_near_avg",
    "spine_color",
    "tick_color",
    "tickline_color",
}


def load_themes() -> dict[str, dict[str, Any]]:
    """Load themes from themes.json file.

    Returns:
        Dictionary mapping theme names to their color configurations.
        Example: {"dark": {...}, "light": {...}}
    """
    global _THEMES_CACHE

    if _THEMES_CACHE is not None:
        return _THEMES_CACHE

    themes_file = Path(__file__).parent / "themes.json"

    with open(themes_file, "r", encoding="utf-8") as f:
        _THEMES_CACHE = json.load(f)

    _LOGGER.debug("Loaded %d themes from themes.json", len(_THEMES_CACHE))
    return _THEMES_CACHE


def get_theme_names() -> list[str]:
    """Get list of available theme names.

    Returns:
        List of theme names (e.g., ["dark", "light"])
    """
    themes = load_themes()
    return list(themes.keys())


def get_theme_config(theme_name: str, custom_theme: dict[str, Any] | None = None) -> dict[str, Any]:
    """Get configuration for a specific theme.

    Args:
        theme_name: Name of the theme to retrieve (e.g., "dark", "light")
        custom_theme: Optional custom theme dictionary that takes precedence over named themes

    Returns:
        Dictionary containing theme color configuration.
        Falls back to "dark" theme if requested theme not found.
    """
    # If custom theme is provided, use it instead of named theme
    if custom_theme is not None:
        _LOGGER.debug("Using custom theme configuration")
        return custom_theme

    themes = load_themes()

    if theme_name not in themes:
        _LOGGER.warning(
            "Theme '%s' not found, falling back to 'dark' theme",
            theme_name
        )
        theme_name = "dark"

    return themes[theme_name]


def validate_custom_theme(theme_config: dict[str, Any]) -> tuple[bool, str]:
    """Validate that a custom theme contains all required fields.

    Args:
        theme_config: Dictionary containing theme configuration

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty string.
    """
    if not isinstance(theme_config, dict):
        return False, "Theme config must be a dictionary"

    missing_fields = REQUIRED_THEME_FIELDS - set(theme_config.keys())

    if missing_fields:
        return False, f"Missing required theme fields: {', '.join(sorted(missing_fields))}"

    return True, ""
