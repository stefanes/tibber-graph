"""User configuration for the Tibber Graph component.

This file imports all defaults from defaults.py and allows you to override
specific settings. Edit this file to customize your Tibber Graph configuration.

Example:
    To change the canvas size, uncomment and modify:
    # CANVAS_WIDTH = 800
    # CANVAS_HEIGHT = 600
"""

# Import all default settings
from .defaults import *

# =========================
# USER CONFIGURATION
# =========================
# Add your custom overrides below this line.
# Any setting from defaults.py can be overridden here.

# Image size configuration
# CANVAS_HEIGHT = 700
# CANVAS_WIDTH = 1200
# FORCE_FIXED_SIZE = True

# X-axis settings
# SHOW_X_TICKS = True
START_AT_MIDNIGHT = False  # Default: True
# X_AXIS_BOTTOM_MARGIN = 0.25
X_AXIS_LABEL_FONT_SIZE = 17  # Default: 12
# X_AXIS_LABEL_ROTATION_DEG = 45
# X_AXIS_LABEL_Y_OFFSET = 0.05
# X_TICK_STEP_HOURS = 3

# Y-axis settings
# SHOW_Y_AXIS = True
# SHOW_Y_GRID = True
Y_AXIS_LABEL_FONT_SIZE = 17  # Default: 11
Y_AXIS_LABEL_PADDING = 11  # Default: 3
Y_AXIS_LABEL_VERTICAL = True  # Default: False
Y_AXIS_LABEL_VERTICAL_ANCHOR = True  # Default: False
Y_AXIS_SIDE = "right"  # Default: "left"
Y_TICK_COUNT = 3  # Default: None
Y_TICK_USE_COLORS = True  # Default: False

# Price labels
CURRENCY_OVERRIDE = "öre"  # Default: None
# LABEL_CURRENT = True
LABEL_CURRENT_AT_TOP = True  # Default: False
# LABEL_CURRENT_AT_TOP_FONT_SIZE = 17
# LABEL_CURRENT_AT_TOP_FONT_WEIGHT = "normal"
# LABEL_CURRENT_AT_TOP_PADDING = 0.035
LABEL_FONT_SIZE = 17  # Default: 12
# LABEL_FONT_WEIGHT = "normal"
# LABEL_MAX = True
LABEL_MAX_BELOW_POINT = True  # Default: False
# LABEL_MIN = True
LABEL_MINMAX_SHOW_PRICE = False  # Default: True
LABEL_SHOW_CURRENCY = False  # Default: True
# LABEL_USE_COLORS = False
# PRICE_DECIMALS = 2
USE_CENTS = True  # Default: False
USE_HOURLY_PRICES = True  # Default: False

# Theme
# THEME = "dark"
# LIGHT_AXIS_LABEL_COLOR = "#000000"
# LIGHT_BACKGROUND_COLOR = "white"
# LIGHT_FILL_ALPHA = 0.25
# LIGHT_FILL_COLOR = "#039be5"
# LIGHT_GRID_ALPHA = 0.25
# LIGHT_GRID_COLOR = "gray"
# LIGHT_LABEL_COLOR = "#000000"
# LIGHT_LABEL_COLOR_AVG = "#fbbf24"
# LIGHT_LABEL_COLOR_MAX = "#ef4444"
# LIGHT_LABEL_COLOR_MIN = "#22c55e"
# LIGHT_LABEL_STROKE = False
# LIGHT_NOWLINE_ALPHA = 0.35
# LIGHT_NOWLINE_COLOR = "r"
# LIGHT_PLOT_LINEWIDTH = 2.0
# LIGHT_PRICE_LINE_COLOR = "#039be5"
# LIGHT_SPINE_COLOR = "#cccccc"
# LIGHT_STYLE_NAME = "ggplot"
# LIGHT_TICK_COLOR = "#000000"
# LIGHT_TICKLINE_COLOR = "#e0e0e0"
# DARK_AXIS_LABEL_COLOR = "#cfd6e6"
# DARK_BACKGROUND_COLOR = "#0b0f14"
# DARK_FILL_ALPHA = 0.18
# DARK_FILL_COLOR = "#7dc3ff"
# DARK_GRID_ALPHA = 0.45
# DARK_GRID_COLOR = "#2a2f36"
# DARK_LABEL_COLOR = "#e6edf3"
# DARK_LABEL_COLOR_AVG = "#fcd34d"
# DARK_LABEL_COLOR_MAX = "#f87171"
# DARK_LABEL_COLOR_MIN = "#6ee7b7"
# DARK_LABEL_STROKE = True
# DARK_NOWLINE_ALPHA = 0.5
# DARK_NOWLINE_COLOR = "#ff6b6b"
# DARK_PLOT_LINEWIDTH = 2.2
# DARK_PRICE_LINE_COLOR = "#7dc3ff"
# DARK_SPINE_COLOR = "#3a4250"
# DARK_STYLE_NAME = "default"
# DARK_TICK_COLOR = "#cfd6e6"
# DARK_TICKLINE_COLOR = "#1f2530"

# Refresh settings
# AUTO_REFRESH_ENABLED = True
# AUTO_REFRESH_INTERVAL_MINUTES = 10
# MIN_REDRAW_INTERVAL_SECONDS = 60

# =========================
# END USER CONFIGURATION
# =========================
