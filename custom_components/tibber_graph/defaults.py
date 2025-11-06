"""Default configuration values for the Tibber Graph component.

These are the fallback values used when options are not configured through
the Home Assistant UI. To customize settings, use the integration's options
flow in the Home Assistant UI (Settings > Devices & Services > Tibber Graph).
"""

# =========================
# DEFAULT CONFIGURATION
# =========================

# General settings
THEME = "dark"                              # Theme: "dark" or "light"
TRANSPARENT_BACKGROUND = False              # Use transparent background with selected theme
CANVAS_WIDTH = 1180
CANVAS_HEIGHT = 820
FORCE_FIXED_SIZE = True                     # Always render at a fixed size (ignores Home Assistant camera size requests)
BOTTOM_MARGIN = 0.14                        # Space reserved for bottom labels
LEFT_MARGIN = 0.12                          # Left margin for the plot area

# X-axis settings
SHOW_X_TICKS = False                        # If True, show x-axis ticks at manual label positions
START_GRAPH_AT = "show_all"                 # Graph start point: "midnight" = start at midnight, "current_hour" = start at current hour, "show_all" = show all available data. See HOURS_TO_SHOW for range behavior.
X_TICK_STEP_HOURS = 3                       # Label every 3 hours
HOURS_TO_SHOW = None                        # Number of hours from anchor point (None = all available data). For 24h midnight-to-midnight: set START_GRAPH_AT="midnight" and HOURS_TO_SHOW=24
SHOW_VERTICAL_GRID = True                   # True = show vertical gridlines, False = hide
X_AXIS_LABEL_Y_OFFSET = 0.05                # Distance below axis (as fraction)

# Y-axis settings
SHOW_Y_AXIS = True                          # True = show Y axis (ticks, labels, spine). Set False to hide
SHOW_Y_AXIS_TICKS = False                   # True = show Y axis tick marks, False = hide
SHOW_HORIZONTAL_GRID = False                # True = show horizontal gridlines, False = hide
SHOW_AVERAGE_PRICE_LINE = True              # True = show dotted line at average price of displayed data, False = hide
CHEAP_PRICE_POINTS = 0                      # Number of lowest-price periods to highlight (0 = none, highlights cheapest hours/quarters)
CHEAP_PRICE_THRESHOLD = 0.0                 # Price threshold for highlighting cheap periods (0.0 = disabled, e.g., 0.5 = 50 öre)
Y_AXIS_LABEL_ROTATION_DEG = 0               # Rotation angle for Y-axis labels (0 = horizontal, 90 = vertical left side, 270 = vertical right side)
Y_AXIS_SIDE = "left"                        # "left" or "right" - which side to draw the Y axis on
Y_TICK_COUNT = None                         # Set to an int to control number of Y-axis ticks (e.g., 5). None = automatic.
Y_TICK_USE_COLORS = False                   # True = color Y-axis ticks (min/avg/max); False = use default tick color
Y_AXIS_LABEL_VERTICAL_ANCHOR = False        # If True, anchor vertical labels at tick; False = center on tick

# Price labels
USE_HOURLY_PRICES = False                   # True = aggregate 15-min prices into hourly averages (4 quarters per hour)
USE_CENTS = False                           # True = display in cents
CURRENCY_OVERRIDE = None                    # Override currency (e.g., "EUR", "SEK", "öre"). None = use Tibber home currency (standard mode) or '¢' (cents mode)
LABEL_CURRENT = True                        # True = show current price label
LABEL_CURRENT_IN_HEADER = True              # True = show current label centered in header; False = show on the graph
LABEL_CURRENT_IN_HEADER_MORE = True         # True = show additional info in header (average price and % to average); requires LABEL_CURRENT_IN_HEADER
LABEL_CURRENT_IN_HEADER_FONT_WEIGHT = "bold"   # "normal" or "bold" (for header current label)
LABEL_CURRENT_IN_HEADER_PADDING = 0.09      # Vertical padding from bottom of text to top of graph area (as fraction, e.g., 0.035 = 3.5%)
LABEL_FONT_SIZE = 11                        # Font size for in-graph price labels (min/max/current)
LABEL_FONT_WEIGHT = "normal"                # "normal" or "bold" (for in-graph labels)
LABEL_MAX = True                            # True = show maximum price label on the graph
LABEL_MAX_BELOW_POINT = False               # True = render max label below data point; False = render above
LABEL_MIN = True                            # True = show minimum price label on the graph
LABEL_MINMAX_SHOW_PRICE = True              # True = show price on min/max labels; False = show only time
LABEL_SHOW_CURRENCY = True                  # True = show currency on price labels (min/max/current).
LABEL_USE_COLORS = False                    # True = color min/max/avg labels (green/red/amber); False = use default label color
PRICE_DECIMALS = None                       # Number of decimals to show for all price displays (None = auto: 2 for standard, 0 for cents)
COLOR_PRICE_LINE_BY_AVERAGE = True          # True = color price line based on average (blue below, amber near, red above); False = use single color
NEAR_AVERAGE_THRESHOLD = 0.25               # Threshold for "near average" color range (±25% from average), used only when COLOR_PRICE_LINE_BY_AVERAGE is enabled

# Refresh settings
AUTO_REFRESH_ENABLED = False                # True = automatically refresh the graph on data interval boundaries (hourly or every 15 min)
AUTO_REFRESH_INTERVAL_MINUTES = 10          # Auto-refresh interval in minutes (set to 10 for every 10 minutes, 1 for every minute, etc.)
MIN_REDRAW_INTERVAL_SECONDS = 60            # Minimum interval between re-renders (seconds)
RENDER_STAGGER_MAX_SECONDS = 0              # Maximum random delay in seconds to stagger entity updates and prevent simultaneous rendering (0 = no staggering)

# =========================
# END DEFAULT CONFIGURATION
# =========================
