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
LABEL_FONT_SIZE = 11                        # Font size for in-graph price labels (min/max/current)
START_GRAPH_AT = "show_all"                 # Graph start point: "midnight" = start at midnight, "current_hour" = start at current hour, "show_all" = show all available data. See HOURS_TO_SHOW for range behavior.
HOURS_TO_SHOW = None                        # Number of hours from anchor point (None = all available data). For 24h midnight-to-midnight: set START_GRAPH_AT="midnight" and HOURS_TO_SHOW=24
CHEAP_PRICE_POINTS = 0                      # Number of lowest-price periods to highlight (0 = none, highlights cheapest hours/quarters)
CHEAP_PRICE_THRESHOLD = 0.0                 # Price threshold for highlighting cheap periods (0.0 = disabled, e.g., 0.5 = 50 öre)
SHOW_AVERAGE_PRICE_LINE = True              # True = show dotted line at average price of displayed data, False = hide
COLOR_PRICE_LINE_BY_AVERAGE = True          # True = color price line based on average (blue below, amber near, red above); False = use single color
BOTTOM_MARGIN = 0.14                        # Space reserved for bottom labels
LEFT_MARGIN = 0.12                          # Left margin for the plot area
NEAR_AVERAGE_THRESHOLD = 0.25               # Threshold for "near average" color range (±25% from average), used only when COLOR_PRICE_LINE_BY_AVERAGE is enabled
COLOR_GRADIENT_INTERPOLATION_STEPS = 10     # Number of interpolation steps for smooth color gradients on vertical segments of colored price line

# Price labels
PRICE_DECIMALS = None                       # Number of decimals to show for all price displays (None = auto: 2 for standard, 0 for cents)
USE_HOURLY_PRICES = False                   # True = aggregate 15-min prices into hourly averages (4 quarters per hour)
USE_CENTS = False                           # True = display in cents
CURRENCY_OVERRIDE = None                    # Override currency (e.g., "€", "SEK", "öre"). None = use Tibber home currency (standard mode) or '¢' (cents mode)
LABEL_SHOW_CURRENCY = True                  # True = show currency on price labels (min/max/current).
LABEL_CURRENT = "on"                        # "on" = show in header with extra info, "on_current_price_only" = show in header (price only), "on_in_graph" = show in graph, "off" = do not show
LABEL_CURRENT_IN_HEADER_FONT_WEIGHT = "bold"   # "normal" or "bold" (for header current label)
LABEL_CURRENT_IN_HEADER_PADDING = 0.09      # Vertical padding from bottom of text to top of graph area (as fraction, e.g., 0.035 = 3.5%)
LABEL_FONT_WEIGHT = "normal"                # "normal" or "bold" (for in-graph labels)
LABEL_MIN = "on"                            # "on" = show min label with price, "on_no_price" = show min label without price, "off" = do not show min label
LABEL_MAX = "on"                            # "on" = show max label with price, "on_no_price" = show max label without price, "off" = do not show max label
LABEL_MAX_BELOW_POINT = False               # True = render max label below data point; False = render above
LABEL_USE_COLORS = False                    # True = color min/max/avg labels; False = use default label color

# X-axis settings
SHOW_X_AXIS = "on"                          # X-axis visibility: "on" = show axis/labels without tick marks, "on_with_tick_marks" = show axis/labels with tick marks, "off" = hide x-axis completely
X_TICK_STEP_HOURS = 3                       # Label every 3 hours
CHEAP_PERIODS_ON_X_AXIS = "off"             # Highlight cheap periods on X-axis: "on" = highlight cheap hours on existing labels, "on_comfy" = show cheap periods in separate row, "on_compact" = show cheap periods on same row, "off" = do not highlight (requires cheap_price_points or cheap_price_threshold > 0)
SHOW_VERTICAL_GRID = True                   # True = show vertical gridlines, False = hide
X_AXIS_LABEL_Y_OFFSET = 0.05                # Distance below axis (as fraction)
CHEAP_PERIOD_BOUNDARY_HOURS = 0             # Internal: Hours from cheap period boundaries to show end time label (0 = use X_TICK_STEP_HOURS, not exposed to UI)
CHEAP_PERIOD_BOUNDARY_HIGHLIGHT = False     # Internal: Make start and end time labels of cheap periods bold in comfy and compact mode (not exposed to UI)

# Y-axis settings
SHOW_Y_AXIS = "on"                          # Y-axis visibility: "on" = show axis/labels without tick marks, "on_with_tick_marks" = show axis/labels with tick marks, "off" = hide y-axis completely
Y_TICK_COUNT = None                         # Set to an int to control number of Y-axis ticks (e.g., 5). None = automatic.
Y_AXIS_LABEL_ROTATION_DEG = 0               # Rotation angle for Y-axis labels (0 = horizontal, 90 = vertical left side, 270 = vertical right side)
Y_AXIS_SIDE = "left"                        # "left" or "right" - which side to draw the Y axis on
Y_TICK_USE_COLORS = False                   # True = color Y-axis ticks (min/avg/max); False = use default tick color
SHOW_HORIZONTAL_GRID = False                # True = show horizontal gridlines, False = hide
Y_AXIS_LABEL_VERTICAL_ANCHOR = False        # If True, anchor vertical labels at tick; False = center on tick

# Refresh settings
REFRESH_MODE = "system"                     # Refresh mode: "system" = update on camera refresh, "system_interval" = update on camera refresh + interval, "interval" = update on interval only, "manual" = manual updates only
MIN_REDRAW_INTERVAL_SECONDS = 60            # Minimum interval between re-renders (seconds)
RENDER_STAGGER_MAX_SECONDS = 0              # Maximum random delay in seconds to stagger entity updates and prevent simultaneous rendering (0 = no staggering)
REFRESH_INTERVAL_DELAY_SECONDS = 30         # Number of seconds after interval boundary to schedule refresh (e.g., 30 = refresh at :00:30, :15:30, :30:30, :45:30 for 15-min intervals)

# =========================
# END DEFAULT CONFIGURATION
# =========================
