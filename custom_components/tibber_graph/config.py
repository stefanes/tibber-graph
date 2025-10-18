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
# CANVAS_HEIGHT = 700  # Default: 700
# CANVAS_WIDTH = 1200  # Default: 1200
# FORCE_FIXED_SIZE = True  # Default: True

# X-axis settings
# SHOW_X_TICKS = True  # Default: True
START_AT_MIDNIGHT = False  # Default: True
# X_AXIS_BOTTOM_MARGIN = 0.25  # Default: 0.25
X_AXIS_LABEL_FONT_SIZE = 17  # Default: 12
# X_AXIS_LABEL_ROTATION_DEG = 45  # Default: 45
# X_AXIS_LABEL_Y_OFFSET = 0.05  # Default: 0.05
# X_TICK_STEP_HOURS = 3  # Default: 3

# Y-axis settings
# SHOW_Y_AXIS = True  # Default: True
# SHOW_Y_GRID = True  # Default: True
Y_AXIS_LABEL_FONT_SIZE = 17  # Default: 11
Y_AXIS_LABEL_PADDING = 11  # Default: 3
Y_AXIS_LABEL_VERTICAL = True  # Default: False
Y_AXIS_LABEL_VERTICAL_ANCHOR = True  # Default: False
Y_AXIS_SIDE = "right"  # Default: "left"
Y_TICK_COUNT = 3  # Default: None
Y_TICK_USE_COLORS = True  # Default: False

# Price labels
CURRENCY_OVERRIDE = "öre"  # Default: None
# LABEL_CURRENT = True  # Default: True
LABEL_CURRENT_AT_TOP = True  # Default: False
# LABEL_CURRENT_AT_TOP_FONT_SIZE = 17  # Default: 17
# LABEL_CURRENT_AT_TOP_FONT_WEIGHT = "normal"  # Default: "normal"
# LABEL_CURRENT_AT_TOP_PADDING = 0.035  # Default: 0.035
LABEL_FONT_SIZE = 17  # Default: 12
# LABEL_FONT_WEIGHT = "normal"  # Default: "normal"
# LABEL_MAX = True  # Default: True
LABEL_MAX_BELOW_POINT = True  # Default: False
# LABEL_MIN = True  # Default: True
LABEL_MINMAX_SHOW_PRICE = False  # Default: True
LABEL_SHOW_CURRENCY = False  # Default: True
# LABEL_USE_COLORS = False  # Default: False
# PRICE_DECIMALS = 2  # Default: 2
USE_CENTS = True  # Default: False
USE_HOURLY_PRICES = True  # Default: False

# Theme
# THEME = "dark"  # Default: "dark"
# LIGHT_AXIS_LABEL_COLOR = "#000000"  # Default: "#000000"
# LIGHT_BACKGROUND_COLOR = "white"  # Default: "white"
# LIGHT_FILL_ALPHA = 0.25  # Default: 0.25
# LIGHT_FILL_COLOR = "#039be5"  # Default: "#039be5"
# LIGHT_GRID_ALPHA = 0.25  # Default: 0.25
# LIGHT_GRID_COLOR = "gray"  # Default: "gray"
# LIGHT_LABEL_COLOR = "#000000"  # Default: "#000000"
# LIGHT_LABEL_COLOR_AVG = "#fbbf24"  # Default: "#fbbf24"
# LIGHT_LABEL_COLOR_MAX = "#ef4444"  # Default: "#ef4444"
# LIGHT_LABEL_COLOR_MIN = "#22c55e"  # Default: "#16a34a"
# LIGHT_LABEL_STROKE = False  # Default: False
# LIGHT_NOWLINE_ALPHA = 0.35  # Default: 0.35
# LIGHT_NOWLINE_COLOR = "r"  # Default: "r"
# LIGHT_PLOT_LINEWIDTH = 2.0  # Default: 2.0
# LIGHT_PRICE_LINE_COLOR = "#039be5"  # Default: "#039be5"
# LIGHT_SPINE_COLOR = "#cccccc"  # Default: "#cccccc"
# LIGHT_STYLE_NAME = "ggplot"  # Default: "ggplot"
# LIGHT_TICK_COLOR = "#000000"  # Default: "#000000"
# LIGHT_TICKLINE_COLOR = "#e0e0e0"  # Default: "#e0e0e0"
# DARK_AXIS_LABEL_COLOR = "#cfd6e6"  # Default: "#cfd6e6"
# DARK_BACKGROUND_COLOR = "#0b0f14"  # Default: "#0b0f14"
# DARK_FILL_ALPHA = 0.18  # Default: 0.18
# DARK_FILL_COLOR = "#7dc3ff"  # Default: "#7dc3ff"
# DARK_GRID_ALPHA = 0.45  # Default: 0.45
# DARK_GRID_COLOR = "#2a2f36"  # Default: "#2a2f36"
# DARK_LABEL_COLOR = "#e6edf3"  # Default: "#e6edf3"
# DARK_LABEL_COLOR_AVG = "#fcd34d"  # Default: "#eab308"
# DARK_LABEL_COLOR_MAX = "#f87171"  # Default: "#fb7185"
# DARK_LABEL_COLOR_MIN = "#6ee7b7"  # Default: "#34d399"
# DARK_LABEL_STROKE = True  # Default: True
# DARK_NOWLINE_ALPHA = 0.5  # Default: 0.5
# DARK_NOWLINE_COLOR = "#ff6b6b"  # Default: "#ff6b6b"
# DARK_PLOT_LINEWIDTH = 2.2  # Default: 2.2
# DARK_PRICE_LINE_COLOR = "#7dc3ff"  # Default: "#7dc3ff"
# DARK_SPINE_COLOR = "#3a4250"  # Default: "#3a4250"
# DARK_STYLE_NAME = "default"  # Default: "default"
# DARK_TICK_COLOR = "#cfd6e6"  # Default: "#cfd6e6"
# DARK_TICKLINE_COLOR = "#1f2530"  # Default: "#1f2530"

# Refresh settings
# AUTO_REFRESH_ENABLED = True  # Default: True
# AUTO_REFRESH_INTERVAL_MINUTES = 10  # Default: 10
# MIN_REDRAW_INTERVAL_SECONDS = 60  # Default: 60

# =========================
# END USER CONFIGURATION
# =========================
