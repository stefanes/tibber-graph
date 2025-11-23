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
    "avgline_color",
    "avgline_style",
    "axis_label_color",
    "background_color",
    "cheap_price_color",
    "cheapline_color",
    "cheapline_style",
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
    """Get configuration for a specific theme and optionally overlay a custom theme.

    If `custom_theme` is provided it will be merged on top of the named built-in theme.
    Properties omitted from `custom_theme` will be taken from the built-in theme. If
    `theme_name` is not found, falls back to the "dark" theme.

    Returns a full theme dict (no missing keys) for safe consumption by renderers.
    """
    themes = load_themes()

    if theme_name not in themes:
        _LOGGER.warning("Theme '%s' not found, falling back to 'dark' theme", theme_name)
        theme_name = "dark"

    base = dict(themes.get(theme_name, {}))

    # If a custom theme is provided, overlay it onto the base theme so omitted
    # properties take their values from the selected built-in theme.
    if custom_theme:
        if not isinstance(custom_theme, dict):
            _LOGGER.warning("Custom theme provided is not a dict; ignoring custom theme")
        else:
            base.update(custom_theme)
            _LOGGER.debug("Applied custom theme overrides on top of theme '%s'", theme_name)

    return base


def validate_custom_theme(theme_config: dict[str, Any]) -> tuple[bool, str]:
    """Validate a custom theme.

    Returns:
        Tuple of (is_valid: bool, error_message: str).
    """
    if not isinstance(theme_config, dict):
        return False, "Theme config must be a dictionary"

    # Only allow keys that exist in built-in themes (prevent typos and unknown props)
    allowed_keys = set()
    for t in load_themes().values():
        allowed_keys.update(t.keys())

    unknown_keys = set(theme_config.keys()) - allowed_keys
    if unknown_keys:
        return False, f"Unknown theme properties: {', '.join(sorted(unknown_keys))}"

    # Helper validators
    def is_color(v: Any) -> bool:
        # Accept strings like '#rrggbb' or 'none' (for transparent background)
        if not isinstance(v, str):
            return False
        if v.lower() == "none":
            return True
        if v.startswith("#") and len(v) in (4, 7):
            # basic hex check (#rgb or #rrggbb)
            try:
                int(v[1:], 16)
                return True
            except ValueError:
                return False
        return False

    def is_linestyle(v: Any) -> bool:
        # Accept matplotlib linestyle strings or tuple dash sequences
        if isinstance(v, str):
            return True
        if isinstance(v, tuple):
            return all(isinstance(x, (int, float)) for x in v)
        return False

    # Type checks for provided properties
    for key, val in theme_config.items():
        if key.endswith("_color") or key == "background_color":
            if not is_color(val):
                return False, f"Invalid color value for '{key}': {val!r}"

        elif key.endswith("_alpha"):
            if not isinstance(val, (int, float)) or not (0.0 <= float(val) <= 1.0):
                return False, f"Invalid alpha value for '{key}': {val!r} (must be 0.0-1.0)"

        elif key in ("label_stroke",):
            if not isinstance(val, bool):
                return False, f"Invalid boolean value for '{key}': {val!r}"

        elif key in ("plot_linewidth",):
            if not isinstance(val, (int, float)) or float(val) < 0:
                return False, f"Invalid numeric value for '{key}': {val!r}"

        elif key in ("avgline_style", "cheapline_style"):
            if not is_linestyle(val):
                return False, f"Invalid linestyle for '{key}': {val!r}"

        else:
            # Other keys are expected to be strings (label color names etc.) — basic acceptance
            # If value types need to be stricter, add explicit checks here.
            pass

    return True, ""
