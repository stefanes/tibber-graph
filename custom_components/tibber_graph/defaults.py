"""Default configuration values for the Tibber Graph component.

These are the fallback values used when options are not configured through
the Home Assistant UI. To customize settings, use the integration's options
flow in the Home Assistant UI (Settings > Devices & Services > Tibber Graph).
"""

# =========================
# DEFAULT CONFIGURATION
# =========================

# General settings
THEME = "dark"                              # Theme: "light" or "dark"
CANVAS_HEIGHT = 700
CANVAS_WIDTH = 1200
FORCE_FIXED_SIZE = True                     # Always render at a fixed size (ignores Home Assistant camera size requests)
BOTTOM_MARGIN = 0.23                        # Space reserved for bottom labels (0.22–0.28)
LEFT_MARGIN = 0.12                          # Left margin for the plot area

# X-axis settings
SHOW_X_TICKS = False                        # If True, show x-axis ticks at manual label positions
START_AT_MIDNIGHT = True                    # True = show from midnight to midnight, False = current hour to last data point
X_AXIS_LABEL_ROTATION_DEG = 45              # Rotation angle for X-axis labels (in degrees)
X_AXIS_LABEL_Y_OFFSET = 0.05                # Distance below axis (as fraction)
X_TICK_STEP_HOURS = 3                       # Label every 3 hours

# Y-axis settings
SHOW_Y_AXIS = True                          # True = show Y axis (ticks, labels, spine). Set False to hide
SHOW_Y_GRID = True                          # True = show horizontal gridlines, False = hide
Y_AXIS_LABEL_ROTATION_DEG = 0               # Rotation angle for Y-axis labels (0 = horizontal, 90 = vertical left side, 270 = vertical right side)
Y_AXIS_LABEL_VERTICAL_ANCHOR = False        # If True, anchor vertical labels at tick; False = center on tick
Y_AXIS_SIDE = "left"                        # "left" or "right" - which side to draw the Y axis on
Y_TICK_COUNT = None                         # Set to an int to control number of Y-axis ticks (e.g., 5). None = automatic.
Y_TICK_USE_COLORS = False                   # True = color Y-axis ticks (min/avg/max); False = use default tick color

# Price labels
CURRENCY_OVERRIDE = None                    # Override currency (e.g., "EUR", "SEK", "öre"). None = use Tibber home currency (standard mode) or '¢' (cents mode)
LABEL_CURRENT = True                        # True = show current price label
LABEL_CURRENT_AT_TOP = False                # True = show current label at top-left corner; False = show on the graph
LABEL_CURRENT_AT_TOP_FONT_WEIGHT = "normal" # "normal" or "bold" (for top-left current label)
LABEL_CURRENT_AT_TOP_PADDING = 0.035        # Vertical padding between top label and graph area (as fraction, e.g., 0.02 = 2%)
LABEL_FONT_SIZE = 11                        # Font size for in-graph price labels (min/max/current)
LABEL_FONT_WEIGHT = "normal"                # "normal" or "bold" (for in-graph labels)
LABEL_MAX = True                            # True = show maximum price label on the graph
LABEL_MAX_BELOW_POINT = False               # True = render max label below data point; False = render above
LABEL_MIN = True                            # True = show minimum price label on the graph
LABEL_MINMAX_SHOW_PRICE = True              # True = show price on min/max labels; False = show only time
LABEL_SHOW_CURRENCY = True                  # True = show currency on price labels (min/max/current).
LABEL_USE_COLORS = False                    # True = color min/max/avg labels (green/red/amber); False = use default label color
PRICE_DECIMALS = None                       # Number of decimals to show for all price displays (None = auto: 2 for standard, 0 for cents)
USE_CENTS = False                           # True = display in cents
USE_HOURLY_PRICES = False                   # True = aggregate 15-min prices into hourly averages (4 quarters per hour)

# Refresh settings
AUTO_REFRESH_ENABLED = False                # True = automatically refresh the chart on data interval boundaries (hourly or every 15 min)
AUTO_REFRESH_INTERVAL_MINUTES = 10          # Auto-refresh interval in minutes (set to 10 for every 10 minutes, 1 for every minute, etc.)
MIN_REDRAW_INTERVAL_SECONDS = 60            # Minimum interval between re-renders (seconds)

# Theme
LIGHT_AXIS_LABEL_COLOR = "#000000"
LIGHT_BACKGROUND_COLOR = "white"
LIGHT_FILL_ALPHA = 0.25
LIGHT_FILL_COLOR = "#039be5"
LIGHT_GRID_ALPHA = 0.25
LIGHT_GRID_COLOR = "gray"
LIGHT_LABEL_COLOR = "#000000"
LIGHT_LABEL_COLOR_AVG = "#fbbf24"
LIGHT_LABEL_COLOR_MAX = "#ef4444"
LIGHT_LABEL_COLOR_MIN = "#16a34a"
LIGHT_LABEL_STROKE = False
LIGHT_NOWLINE_ALPHA = 0.35
LIGHT_NOWLINE_COLOR = "r"
LIGHT_PLOT_LINEWIDTH = 2.0
LIGHT_PRICE_LINE_COLOR = "#039be5"
LIGHT_SPINE_COLOR = "#cccccc"
LIGHT_STYLE_NAME = "ggplot"
LIGHT_TICK_COLOR = "#000000"
LIGHT_TICKLINE_COLOR = "#e0e0e0"
DARK_AXIS_LABEL_COLOR = "#cfd6e6"
DARK_BACKGROUND_COLOR = "#0b0f14"
DARK_FILL_ALPHA = 0.18
DARK_FILL_COLOR = "#7dc3ff"
DARK_GRID_ALPHA = 0.45
DARK_GRID_COLOR = "#2a2f36"
DARK_LABEL_COLOR = "#e6edf3"
DARK_LABEL_COLOR_AVG = "#eab308"
DARK_LABEL_COLOR_MAX = "#fb7185"
DARK_LABEL_COLOR_MIN = "#34d399"
DARK_LABEL_STROKE = True
DARK_NOWLINE_ALPHA = 0.5
DARK_NOWLINE_COLOR = "#ff6b6b"
DARK_PLOT_LINEWIDTH = 2.2
DARK_PRICE_LINE_COLOR = "#7dc3ff"
DARK_SPINE_COLOR = "#3a4250"
DARK_STYLE_NAME = "default"
DARK_TICK_COLOR = "#cfd6e6"
DARK_TICKLINE_COLOR = "#1f2530"

# =========================
# END DEFAULT CONFIGURATION
# =========================
