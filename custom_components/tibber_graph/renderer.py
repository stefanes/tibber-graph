"""Rendering logic for Tibber price graphs using matplotlib."""
import datetime

import matplotlib
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# Import helper functions
from .helpers import ensure_timezone

# Import default constants from const.py for fallback values
from .const import (
    DEFAULT_THEME as THEME,
    DEFAULT_TRANSPARENT_BACKGROUND as TRANSPARENT_BACKGROUND,
    DEFAULT_CANVAS_WIDTH as CANVAS_WIDTH,
    DEFAULT_CANVAS_HEIGHT as CANVAS_HEIGHT,
    DEFAULT_FORCE_FIXED_SIZE as FORCE_FIXED_SIZE,
    DEFAULT_CHEAP_PRICE_POINTS as CHEAP_PRICE_POINTS,
    DEFAULT_CHEAP_PRICE_THRESHOLD as CHEAP_PRICE_THRESHOLD,
    DEFAULT_BOTTOM_MARGIN as BOTTOM_MARGIN,
    DEFAULT_LEFT_MARGIN as LEFT_MARGIN,
    DEFAULT_X_AXIS_LABEL_Y_OFFSET as X_AXIS_LABEL_Y_OFFSET,
    DEFAULT_SHOW_X_AXIS as SHOW_X_AXIS,
    DEFAULT_CHEAP_PERIODS_ON_X_AXIS as CHEAP_PERIODS_ON_X_AXIS,
    DEFAULT_START_GRAPH_AT as START_GRAPH_AT,
    DEFAULT_X_TICK_STEP_HOURS as X_TICK_STEP_HOURS,
    DEFAULT_HOURS_TO_SHOW as HOURS_TO_SHOW,
    DEFAULT_SHOW_VERTICAL_GRID as SHOW_VERTICAL_GRID,
    DEFAULT_CHEAP_PERIOD_BOUNDARY_HOURS as CHEAP_PERIOD_BOUNDARY_HOURS,
    DEFAULT_CHEAP_PERIOD_BOUNDARY_HIGHLIGHT as CHEAP_PERIOD_BOUNDARY_HIGHLIGHT,
    DEFAULT_SHOW_Y_AXIS as SHOW_Y_AXIS,
    DEFAULT_SHOW_HORIZONTAL_GRID as SHOW_HORIZONTAL_GRID,
    DEFAULT_SHOW_AVERAGE_PRICE_LINE as SHOW_AVERAGE_PRICE_LINE,
    DEFAULT_Y_AXIS_LABEL_ROTATION_DEG as Y_AXIS_LABEL_ROTATION_DEG,
    DEFAULT_Y_AXIS_LABEL_VERTICAL_ANCHOR as Y_AXIS_LABEL_VERTICAL_ANCHOR,
    DEFAULT_Y_AXIS_SIDE as Y_AXIS_SIDE,
    DEFAULT_Y_TICK_COUNT as Y_TICK_COUNT,
    DEFAULT_Y_TICK_USE_COLORS as Y_TICK_USE_COLORS,
    DEFAULT_USE_CENTS as USE_CENTS,
    DEFAULT_CURRENCY_OVERRIDE as CURRENCY_OVERRIDE,
    DEFAULT_LABEL_CURRENT as LABEL_CURRENT,
    DEFAULT_LABEL_CURRENT_IN_HEADER_FONT_WEIGHT as LABEL_CURRENT_IN_HEADER_FONT_WEIGHT,
    DEFAULT_LABEL_CURRENT_IN_HEADER_PADDING as LABEL_CURRENT_IN_HEADER_PADDING,
    DEFAULT_LABEL_FONT_SIZE as LABEL_FONT_SIZE,
    DEFAULT_LABEL_FONT_WEIGHT as LABEL_FONT_WEIGHT,
    DEFAULT_LABEL_MAX as LABEL_MAX,
    DEFAULT_LABEL_MAX_BELOW_POINT as LABEL_MAX_BELOW_POINT,
    DEFAULT_LABEL_MIN as LABEL_MIN,
    DEFAULT_LABEL_SHOW_CURRENCY as LABEL_SHOW_CURRENCY,
    DEFAULT_LABEL_USE_COLORS as LABEL_USE_COLORS,
    DEFAULT_PRICE_DECIMALS as PRICE_DECIMALS,
    DEFAULT_COLOR_PRICE_LINE_BY_AVERAGE as COLOR_PRICE_LINE_BY_AVERAGE,
    DEFAULT_NEAR_AVERAGE_THRESHOLD as NEAR_AVERAGE_THRESHOLD,
    DEFAULT_COLOR_GRADIENT_INTERPOLATION_STEPS as COLOR_GRADIENT_INTERPOLATION_STEPS,
    START_GRAPH_AT_MIDNIGHT,
    START_GRAPH_AT_CURRENT_HOUR,
    START_GRAPH_AT_SHOW_ALL,
    LABEL_CURRENT_ON,
    LABEL_CURRENT_ON_CURRENT_PRICE_ONLY,
    LABEL_CURRENT_ON_IN_GRAPH,
    LABEL_CURRENT_ON_IN_GRAPH_NO_PRICE,
    LABEL_CURRENT_OFF,
    SHOW_X_AXIS_ON,
    SHOW_X_AXIS_ON_WITH_TICK_MARKS,
    SHOW_X_AXIS_OFF,
    SHOW_Y_AXIS_ON,
    SHOW_Y_AXIS_ON_WITH_TICK_MARKS,
    SHOW_Y_AXIS_OFF,
    LABEL_MAX_ON,
    LABEL_MAX_ON_NO_PRICE,
    LABEL_MAX_OFF,
    LABEL_MIN_ON,
    LABEL_MIN_ON_NO_PRICE,
    LABEL_MIN_OFF,
    CHEAP_PERIODS_ON_X_AXIS_ON,
    CHEAP_PERIODS_ON_X_AXIS_ON_COMFY,
    CHEAP_PERIODS_ON_X_AXIS_ON_COMPACT,
    CHEAP_PERIODS_ON_X_AXIS_OFF,
)

# Import theme loader for dynamic theme selection
from .themes import get_theme_config

# Matplotlib heavy imports: import once at module load to reduce per-render overhead
matplotlib.use("Agg")

# Apply global rc settings once
plt.rcdefaults()
plt.rcParams.update({'font.size': 12})


def _split_past_future_data(dates_plot, prices_plot, now_local):
    """Split price data into past and future sections at current time.

    Ensures continuity at the "now" point by adding interpolation points.

    Args:
        dates_plot: List of datetime objects
        prices_plot: List of price values
        now_local: Current local time as datetime

    Returns:
        Tuple of (past_dates, past_prices, future_dates, future_prices)
    """
    # Validate input data
    if not dates_plot or not prices_plot:
        return [], [], [], []
    if len(dates_plot) != len(prices_plot):
        return [], [], [], []

    past_dates = []
    past_prices = []
    future_dates = []
    future_prices = []

    # Find the current hour's price (the hour that contains "now")
    # This is the last data point that starts at or before "now"
    current_hour_price = None
    for i, (d, p) in enumerate(zip(dates_plot, prices_plot)):
        if d <= now_local:
            current_hour_price = p
            past_dates.append(d)
            past_prices.append(p)
        if d >= now_local:
            future_dates.append(d)
            future_prices.append(p)

    # Ensure continuity at the "now" point using the current hour's price
    if past_dates and future_dates:
        if past_dates[-1] != now_local and future_dates[0] != now_local:
            # Use the current hour's price (the hour containing "now") for both continuity points
            if current_hour_price is not None:
                past_dates.append(now_local)
                past_prices.append(current_hour_price)
                future_dates.insert(0, now_local)
                future_prices.insert(0, current_hour_price)

    return past_dates, past_prices, future_dates, future_prices


def _draw_colored_price_line(ax, dates, prices, average_price, threshold,
                             color_below, color_near, color_above, linewidth):
    """Draw price line with color gradients based on position relative to average.

    Args:
        ax: matplotlib axes object
        dates: List of datetime objects
        prices: List of price values
        average_price: Average price for color calculation
        threshold: Threshold percentage for color zones
        color_below: Color for prices below average
        color_near: Color for prices near average
        color_above: Color for prices above average
        linewidth: Width of the price line
    """
    # Validate input data to prevent rendering errors
    if not dates or not prices or len(dates) <= 1 or len(prices) <= 1:
        return
    if len(dates) != len(prices):
        return

    for i in range(len(dates) - 1):
        color = _get_price_color(prices[i], average_price, threshold,
                                color_below, color_near, color_above)
        # Draw horizontal segment
        ax.plot([dates[i], dates[i + 1]], [prices[i], prices[i]],
               color=color, linewidth=linewidth, zorder=4)

        # Draw vertical segment with interpolated color
        if i + 1 < len(prices) - 1:
            # Interpolate color for vertical segment between current and next price
            color_next = _get_price_color(prices[i + 1], average_price, threshold,
                                          color_below, color_near, color_above)
            # Create gradient on vertical segment
            n_points = COLOR_GRADIENT_INTERPOLATION_STEPS
            y_vals = np.linspace(prices[i], prices[i + 1], n_points)
            for j in range(n_points - 1):
                ratio = j / (n_points - 1)
                interp_color = tuple(color[k] + (color_next[k] - color[k]) * ratio for k in range(3))
                ax.plot([dates[i + 1], dates[i + 1]],
                       [y_vals[j], y_vals[j + 1]],
                       color=interp_color, linewidth=linewidth, zorder=4)
        else:
            # Last vertical segment
            ax.plot([dates[i + 1], dates[i + 1]],
                   [prices[i], prices[i + 1]],
                   color=color, linewidth=linewidth, zorder=4)


def _calculate_end_hour(start_hour, hours_to_show, dates_plot, default_end):
    """Calculate end hour with optional hours limit.

    Args:
        start_hour: Start time as datetime
        hours_to_show: Maximum hours to show (None for no limit)
        dates_plot: List of available data points
        default_end: Default end time if no limit and no data

    Returns:
        End hour as datetime with timezone
    """
    if hours_to_show is not None and hours_to_show > 0:
        hours_end = start_hour + datetime.timedelta(hours=hours_to_show)
        last_data_point = dates_plot[-1] if dates_plot else default_end
        last_data_point = ensure_timezone(last_data_point)
        return min(hours_end, last_data_point)
    else:
        end_hour = dates_plot[-1] if dates_plot else default_end
        return ensure_timezone(end_hour)


def _get_price_color(price, average_price, threshold_pct, color_below, color_near, color_above):
    """Get color for a price based on its position relative to average.

    Args:
        price: Price value to colorize
        average_price: Average price for comparison
        threshold_pct: Threshold percentage (e.g., 0.25 for ±25%)
        color_below: Color for prices far below average
        color_near: Color for prices near average
        color_above: Color for prices far above average

    Returns:
        RGB tuple color with smooth gradient transitions
    """
    import matplotlib.colors as mcolors

    threshold_lower = average_price * (1 - threshold_pct)
    threshold_upper = average_price * (1 + threshold_pct)

    def interpolate_color(color1, color2, ratio):
        """Smoothly interpolate between two hex colors."""
        c1 = mcolors.to_rgb(color1)
        c2 = mcolors.to_rgb(color2)
        return tuple(c1[i] + (c2[i] - c1[i]) * ratio for i in range(3))

    if price >= threshold_upper:
        # Far above average: interpolate from amber to red
        ratio = min((price - threshold_upper) / max(average_price * 0.5, 0.01), 1.0)
        return interpolate_color(color_near, color_above, ratio)
    elif price >= average_price:
        # Slightly above average: interpolate from amber to amber (stay in near-average color)
        ratio = (price - average_price) / (threshold_upper - average_price)
        return interpolate_color(color_near, color_near, ratio)
    elif price >= threshold_lower:
        # Slightly below average: interpolate from blue to amber
        ratio = (price - threshold_lower) / (average_price - threshold_lower)
        return interpolate_color(color_below, color_near, ratio)
    else:
        # Far below average: stay blue
        return mcolors.to_rgb(color_below)


def render_plot_to_path(
    width,
    height,
    dates_plot,
    prices_plot,
    dates_raw,
    prices_raw,
    now_local,
    idx,
    currency,
    out_path,
    render_options=None,
    translations=None,
):
    """Render and save the matplotlib price graph.

    Args:
        width: Canvas width in pixels
        height: Canvas height in pixels
        dates_plot: List of datetime objects for plotting (includes extra point for step plot)
        prices_plot: List of prices for plotting (includes extra point for step plot)
        dates_raw: Original list of datetime objects (raw data)
        prices_raw: Original list of prices (raw data)
        now_local: Current local time as datetime
        idx: Index of current price in raw data
        currency: Currency code string (e.g., "€", "SEK", "öre")
        out_path: Output file path for the rendered image
        render_options: Optional dict of rendering options to override defaults.py values
        translations: Optional dict of translated strings for rendered labels (e.g., {"label_at": "at"})
    """
    # Matplotlib imports and rc settings are prepared at module import to
    # minimize per-render overhead.
    # Use the module-level plt, mticker, pe that were imported earlier.

    # Apply render options if provided, otherwise use global config values
    if render_options is None:
        render_options = {}

    # Extract translations with fallbacks to English
    if translations is None:
        translations = {}
    label_at = translations.get("label_at", "at")
    label_avg = translations.get("label_avg", "avg.")

    # Get option with fallback to global config
    def get_opt(key, global_var):
        return render_options.get(key, global_var)

    # Extract all configurable options from render_options (or use defaults)
    # General settings
    THEME_OPT = get_opt("theme", THEME)
    CANVAS_WIDTH_OPT = get_opt("canvas_width", CANVAS_WIDTH)
    CANVAS_HEIGHT_OPT = get_opt("canvas_height", CANVAS_HEIGHT)
    FORCE_FIXED_SIZE_OPT = get_opt("force_fixed_size", FORCE_FIXED_SIZE)
    CHEAP_PRICE_POINTS_OPT = get_opt("cheap_price_points", CHEAP_PRICE_POINTS)
    CHEAP_PRICE_THRESHOLD_OPT = get_opt("cheap_price_threshold", CHEAP_PRICE_THRESHOLD)
    BOTTOM_MARGIN_OPT = get_opt("bottom_margin", BOTTOM_MARGIN)
    LEFT_MARGIN_OPT = get_opt("left_margin", LEFT_MARGIN)
    # X-axis settings
    SHOW_X_AXIS_OPT = get_opt("show_x_axis", SHOW_X_AXIS)
    CHEAP_PERIODS_ON_X_AXIS_OPT = get_opt("cheap_periods_on_x_axis", CHEAP_PERIODS_ON_X_AXIS)
    START_GRAPH_AT_OPT = get_opt("start_graph_at", START_GRAPH_AT)
    X_TICK_STEP_HOURS_OPT = get_opt("x_tick_step_hours", X_TICK_STEP_HOURS)
    HOURS_TO_SHOW_OPT = get_opt("hours_to_show", HOURS_TO_SHOW)
    SHOW_VERTICAL_GRID_OPT = get_opt("show_vertical_grid", SHOW_VERTICAL_GRID)
    CHEAP_PERIOD_BOUNDARY_HIGHLIGHT_OPT = get_opt("cheap_period_boundary_highlight", CHEAP_PERIOD_BOUNDARY_HIGHLIGHT)
    # Y-axis settings
    SHOW_Y_AXIS_OPT = get_opt("show_y_axis", SHOW_Y_AXIS)
    SHOW_HORIZONTAL_GRID_OPT = get_opt("show_horizontal_grid", SHOW_HORIZONTAL_GRID)
    SHOW_AVERAGE_PRICE_LINE_OPT = get_opt("show_average_price_line", SHOW_AVERAGE_PRICE_LINE)
    Y_AXIS_LABEL_ROTATION_DEG_OPT = get_opt("y_axis_label_rotation_deg", Y_AXIS_LABEL_ROTATION_DEG)
    Y_AXIS_LABEL_VERTICAL_ANCHOR_OPT = get_opt("y_axis_label_vertical_anchor", Y_AXIS_LABEL_VERTICAL_ANCHOR)
    Y_AXIS_SIDE_OPT = get_opt("y_axis_side", Y_AXIS_SIDE)
    Y_TICK_COUNT_OPT = get_opt("y_tick_count", Y_TICK_COUNT)
    Y_TICK_USE_COLORS_OPT = get_opt("y_tick_use_colors", Y_TICK_USE_COLORS)
    # Price labels
    USE_CENTS_OPT = get_opt("use_cents", USE_CENTS)
    CURRENCY_OVERRIDE_OPT = get_opt("currency_override", CURRENCY_OVERRIDE)
    LABEL_CURRENT_OPT = get_opt("label_current", LABEL_CURRENT)
    LABEL_CURRENT_IN_HEADER_FONT_WEIGHT_OPT = get_opt("label_current_in_header_font_weight", LABEL_CURRENT_IN_HEADER_FONT_WEIGHT)
    LABEL_CURRENT_IN_HEADER_PADDING_OPT = get_opt("label_current_in_header_padding", LABEL_CURRENT_IN_HEADER_PADDING)
    LABEL_FONT_SIZE_OPT = get_opt("label_font_size", LABEL_FONT_SIZE)
    LABEL_FONT_WEIGHT_OPT = get_opt("label_font_weight", LABEL_FONT_WEIGHT)
    LABEL_MAX_OPT = get_opt("label_max", LABEL_MAX)
    LABEL_MAX_BELOW_POINT_OPT = get_opt("label_max_below_point", LABEL_MAX_BELOW_POINT)
    LABEL_MIN_OPT = get_opt("label_min", LABEL_MIN)
    LABEL_SHOW_CURRENCY_OPT = get_opt("label_show_currency", LABEL_SHOW_CURRENCY)
    LABEL_USE_COLORS_OPT = get_opt("label_use_colors", LABEL_USE_COLORS)
    PRICE_DECIMALS_OPT = get_opt("price_decimals", PRICE_DECIMALS)
    COLOR_PRICE_LINE_BY_AVERAGE_OPT = get_opt("color_price_line_by_average", COLOR_PRICE_LINE_BY_AVERAGE)

    # Auto-determine price_decimals if not explicitly set (None = auto)
    if PRICE_DECIMALS_OPT is None:
        PRICE_DECIMALS_OPT = 0 if USE_CENTS_OPT else 2

    # Get transparent background option
    TRANSPARENT_BACKGROUND_OPT = get_opt("transparent_background", TRANSPARENT_BACKGROUND)

    # Load theme configuration from themes.json or custom theme
    CUSTOM_THEME_OPT = get_opt("custom_theme", None)
    theme_config = get_theme_config(THEME_OPT, CUSTOM_THEME_OPT)

    # Extract theme colors from configuration
    CHEAP_PRICE_COLOR = theme_config["cheap_price_color"]
    FILL_ALPHA = theme_config["fill_alpha"]
    FILL_COLOR = theme_config["fill_color"]
    GRID_ALPHA = theme_config["grid_alpha"]
    GRID_COLOR = theme_config["grid_color"]
    LABEL_COLOR = theme_config["label_color"]
    NOWLINE_ALPHA = theme_config["nowline_alpha"]
    NOWLINE_COLOR = theme_config["nowline_color"]
    PLOT_LINEWIDTH = theme_config["plot_linewidth"]
    PRICE_LINE_COLOR = theme_config["price_line_color"]
    SPINE_COLOR = theme_config["spine_color"]
    TICK_COLOR = theme_config["tick_color"]
    TICKLINE_COLOR = theme_config["tickline_color"]
    AXIS_LABEL_COLOR = theme_config["axis_label_color"]
    LABEL_STROKE = theme_config["label_stroke"]
    LABEL_COLOR_MIN = theme_config["label_color_min"]
    LABEL_COLOR_MAX = theme_config["label_color_max"]
    LABEL_COLOR_AVG = theme_config["label_color_avg"]
    PRICE_LINE_COLOR_ABOVE_AVG = theme_config["price_line_color_above_avg"]
    PRICE_LINE_COLOR_BELOW_AVG = theme_config["price_line_color_below_avg"]
    PRICE_LINE_COLOR_NEAR_AVG = theme_config["price_line_color_near_avg"]

    # Handle transparent background
    if TRANSPARENT_BACKGROUND_OPT:
        BACKGROUND_COLOR = "none"
    else:
        BACKGROUND_COLOR = theme_config["background_color"]

    # Validate input data early to prevent rendering with empty/invalid data
    if not dates_plot or not prices_plot or len(dates_plot) < 2 or len(prices_plot) < 2:
        # Data is invalid - do not render to prevent matplotlib errors
        # Return without modifying the output file to preserve last valid render
        return
    if len(dates_plot) != len(prices_plot):
        # Data length mismatch - cannot render safely
        # Return without modifying the output file to preserve last valid render
        return

    # Clean up any existing figures before creating new ones
    plt.close("all")

    fig_w = (CANVAS_WIDTH_OPT if FORCE_FIXED_SIZE_OPT else width) / 200
    fig_h = (CANVAS_HEIGHT_OPT if FORCE_FIXED_SIZE_OPT else height) / 200

    # Create new figure with explicit reference
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=200)
    fig.patch.set_facecolor(BACKGROUND_COLOR)

    # Create axes
    ax = fig.add_subplot(111)
    ax.clear()

    # Set background color after clearing
    ax.set_facecolor(BACKGROUND_COLOR)

    # Determine Y-axis visibility and tick marks from dropdown option
    show_y_axis_visible = SHOW_Y_AXIS_OPT != SHOW_Y_AXIS_OFF
    show_y_axis_tick_marks = SHOW_Y_AXIS_OPT == SHOW_Y_AXIS_ON_WITH_TICK_MARKS

    # Style spines and tick colors and place Y axis on configured side
    for name, spine in ax.spines.items():
        spine.set_edgecolor(SPINE_COLOR)
        # Control visibility of left/right spines based on configured side
        if name in ("left", "right"):
            if not show_y_axis_visible:
                spine.set_visible(False)
            else:
                # Show only the configured side and hide the opposite
                if name == Y_AXIS_SIDE_OPT:
                    spine.set_visible(True)
                else:
                    spine.set_visible(False)

    # Configure Y ticks on chosen side
    if show_y_axis_visible:
        if Y_AXIS_SIDE_OPT == "left":
            ax.yaxis.tick_left()
        else:
            ax.yaxis.tick_right()

    y_rotation = Y_AXIS_LABEL_ROTATION_DEG_OPT

    # Calculate padding dynamically based on font size
    # Formula: padding = (font_size * 2 + 5) / 3
    # This gives: size 11→pad 9, size 13→pad 10, size 17→pad 13, size 20→pad 15
    # Use dynamic padding only when labels are rotated (non-zero rotation) and anchor mode is enabled
    y_padding = int((LABEL_FONT_SIZE_OPT * 2 + 5) / 3) if (Y_AXIS_LABEL_ROTATION_DEG_OPT != 0 and Y_AXIS_LABEL_VERTICAL_ANCHOR_OPT) else 3

    ax.tick_params(
        axis="y",
        colors=TICK_COLOR,
        labelleft=show_y_axis_visible and Y_AXIS_SIDE_OPT == "left",
        labelright=show_y_axis_visible and Y_AXIS_SIDE_OPT == "right",
        left=show_y_axis_visible and show_y_axis_tick_marks and Y_AXIS_SIDE_OPT == "left",
        right=show_y_axis_visible and show_y_axis_tick_marks and Y_AXIS_SIDE_OPT == "right",
        labelsize=(LABEL_FONT_SIZE_OPT),
        rotation=y_rotation,
        pad=y_padding,
    )

    # Set rotation_mode for rotated labels based on anchor setting
    # Only apply rotation_mode when labels are actually rotated (non-zero rotation)
    if Y_AXIS_LABEL_ROTATION_DEG_OPT != 0:
        for label in ax.yaxis.get_ticklabels():
            # 'anchor' mode aligns label edge with tick, 'default' centers label on tick
            label.set_rotation_mode('anchor' if Y_AXIS_LABEL_VERTICAL_ANCHOR_OPT else 'default')

    # Optional grid lines
    if SHOW_HORIZONTAL_GRID_OPT and SHOW_VERTICAL_GRID_OPT:
        # Show both horizontal and vertical grid lines
        ax.grid(which="major", axis="both", linestyle="-", color=GRID_COLOR, alpha=GRID_ALPHA, zorder=2)
    elif SHOW_HORIZONTAL_GRID_OPT:
        # Show only horizontal grid lines
        ax.grid(which="major", axis="y", linestyle="-", color=GRID_COLOR, alpha=GRID_ALPHA, zorder=2)
    elif SHOW_VERTICAL_GRID_OPT:
        # Show only vertical grid lines
        ax.grid(which="major", axis="x", linestyle="-", color=GRID_COLOR, alpha=GRID_ALPHA, zorder=2)
    else:
        # Hide all grid lines
        ax.grid(False)

    # Optional average price line (drawn at same z-order as grid lines)
    # This will be drawn after filtering visible prices, so we defer it until later

    # Disable auto X-ticks (we'll draw them manually). Don't set left labels here to avoid
    # interfering with Y_AXIS_SIDE; that is handled per-axis above.
    # IMPORTANT: Use ax.tick_params() not plt.tick_params() to avoid affecting global state
    ax.tick_params(axis="both", which="both", bottom=False, labelbottom=False)

    # Price line and fill will be drawn after determining time range and "now" visibility
    # Cheap price point highlights will be drawn after determining visible data (at z-order 0.5, between background and fill)

    # Define X-range: show from start point to end point based on configuration
    if START_GRAPH_AT_OPT == START_GRAPH_AT_MIDNIGHT:
        # Start at local midnight
        start_hour = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        start_hour = ensure_timezone(start_hour)

        # Calculate end hour with optional hours limit
        default_end = start_hour + datetime.timedelta(days=1)
        end_hour = _calculate_end_hour(start_hour, HOURS_TO_SHOW_OPT, dates_plot, default_end)
    elif START_GRAPH_AT_OPT == START_GRAPH_AT_CURRENT_HOUR:
        # Start one hour before the current hour and show data up to the last available point
        start_hour = now_local.replace(minute=0, second=0, microsecond=0) - datetime.timedelta(hours=1)
        start_hour = ensure_timezone(start_hour)

        # Calculate end hour with optional hours limit
        default_end = start_hour + datetime.timedelta(hours=2)
        end_hour = _calculate_end_hour(start_hour, HOURS_TO_SHOW_OPT, dates_plot, default_end)

        # If the last data point is before the start_hour, ensure a minimal span
        if end_hour <= start_hour:
            end_hour = start_hour + datetime.timedelta(hours=2)
    else:  # START_GRAPH_AT_SHOW_ALL
        # Show all available data from first to last data point
        if dates_plot:
            start_hour = ensure_timezone(dates_plot[0])
            end_hour = ensure_timezone(dates_plot[-1])
        else:
            # Fallback if no data
            start_hour = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
            start_hour = ensure_timezone(start_hour)
            end_hour = start_hour + datetime.timedelta(days=1)

        # Apply hours limit if configured (even in show_all mode)
        if HOURS_TO_SHOW_OPT is not None and HOURS_TO_SHOW_OPT > 0:
            hours_end = start_hour + datetime.timedelta(hours=HOURS_TO_SHOW_OPT)
            end_hour = min(hours_end, end_hour)

    # Check if "now" marker is visible within the time range
    now_is_visible = start_hour <= now_local <= end_hour

    # Compute visible prices from the plotted points (dates_plot/prices_plot)
    # Use numeric timestamps instead of relying on hour values so ranges that
    # cross midnight (and thus wrap hour numbers) are handled correctly.
    start_ts = start_hour.timestamp()
    end_ts = end_hour.timestamp()

    # For "Current hour" mode, determine the calculation start time (excluding cosmetic hour)
    # The cosmetic hour is the extra hour shown before the current hour for visual continuity
    if START_GRAPH_AT_OPT == START_GRAPH_AT_CURRENT_HOUR:
        # Calculations should start from current hour, not the cosmetic hour before
        calc_start_hour = now_local.replace(minute=0, second=0, microsecond=0)
        calc_start_ts = calc_start_hour.timestamp()
    else:
        # For other modes, calculations start from the display start
        calc_start_ts = start_ts

    # Initialize data lists
    visible_prices = []
    visible_indices = []
    calc_prices = []
    calc_indices = []

    # Filter visible data in one pass - build both prices and indices lists simultaneously
    for i, (d, p) in enumerate(zip(dates_plot, prices_plot)):
        if start_ts <= d.timestamp() <= end_ts:
            visible_prices.append(p)
            # Only track indices that correspond to raw data (plot has one extra point)
            if i < len(dates_raw):
                visible_indices.append(i)
                # For calculation data, check if within calculation range
                if calc_start_ts <= d.timestamp() <= end_ts:
                    calc_prices.append(p)
                    calc_indices.append(i)

    # Fallback if no visible data found
    if not visible_prices:
        visible_prices = prices_plot or prices_raw or [0]
    if not visible_indices and prices_raw:
        visible_indices = list(range(len(prices_raw)))

    # Fallback for calculation data
    if not calc_prices:
        calc_prices = visible_prices
    if not calc_indices:
        calc_indices = visible_indices

    # Determine step size for each period (quarter or hour) - needed for cheap price and X-axis ticks
    if dates_raw and len(dates_raw) >= 2:
        step_minutes = int((dates_raw[1] - dates_raw[0]).total_seconds() // 60) or 15
    else:
        step_minutes = 15
    period_duration = datetime.timedelta(minutes=step_minutes)

    # Identify and draw cheap price point highlights if configured
    # This is done before drawing the price line and fill so highlights appear behind the graph
    # Highlights are shown when either CHEAP_PRICE_POINTS_OPT > 0 or CHEAP_PRICE_THRESHOLD_OPT > 0
    if (CHEAP_PRICE_POINTS_OPT > 0 or CHEAP_PRICE_THRESHOLD_OPT > 0) and dates_raw and prices_raw:
        # Group all price data by day (not just visible data)
        # This ensures we identify the cheapest periods per day across all available data
        from collections import defaultdict
        prices_by_day = defaultdict(list)

        for i, d in enumerate(dates_raw):
            day_key = d.date()  # Group by date (ignoring time)
            prices_by_day[day_key].append(i)

        # For each day, find cheap periods based on configured criteria
        cheap_indices_all_days = []
        for day_key, day_indices in prices_by_day.items():
            # Sort indices by price (ascending) for this day
            sorted_day_indices = sorted(day_indices, key=lambda i: prices_raw[i])

            # Start with the N cheapest periods (if cheap_price_points is set)
            cheap_for_day = set()
            if CHEAP_PRICE_POINTS_OPT > 0:
                # Always include the N cheapest periods
                cheap_for_day.update(sorted_day_indices[:min(CHEAP_PRICE_POINTS_OPT, len(sorted_day_indices))])

            # Additionally include all periods below the threshold (if threshold is set)
            if CHEAP_PRICE_THRESHOLD_OPT > 0:
                cheap_for_day.update([i for i in sorted_day_indices if prices_raw[i] < CHEAP_PRICE_THRESHOLD_OPT])

            cheap_indices_all_days.extend(cheap_for_day)

        # Draw background highlights for cheap periods (only if they're in the visible range)
        for cheap_idx in cheap_indices_all_days:
            period_start = dates_raw[cheap_idx]
            period_end = period_start + period_duration

            # Only draw if the period is within the visible time range
            if period_start <= end_hour and period_end >= start_hour:
                # Determine if this period is in the past (for dimming)
                is_past = period_end <= now_local

                # Draw the background rectangle
                # Use dimmed color for past periods
                if is_past:
                    alpha = 0.3  # Dimmed for past
                else:
                    alpha = 0.6  # Bright for future

                ax.axvspan(
                    period_start,
                    period_end,
                    facecolor=CHEAP_PRICE_COLOR,
                    alpha=alpha,
                    zorder=3,  # Above grid lines (z=2) but below price line (z=4)
                )

    # Pre-calculate average price once if needed (used multiple times below)
    average_price = None
    if (COLOR_PRICE_LINE_BY_AVERAGE_OPT or SHOW_AVERAGE_PRICE_LINE_OPT) and calc_prices and len(calc_prices) > 0:
        average_price = sum(calc_prices) / len(calc_prices)

    # Draw price line, fill, and "now" line based on visibility
    # If COLOR_PRICE_LINE_BY_AVERAGE is enabled, color future segments with gradient transitions
    if COLOR_PRICE_LINE_BY_AVERAGE_OPT and average_price is not None:

        if now_is_visible:
            # Split the data into past (dimmed) and future (bright) sections
            past_dates, past_prices, future_dates, future_prices = _split_past_future_data(
                dates_plot, prices_plot, now_local
            )

            # Check if split produced valid sections
            past_has_data = past_dates and past_prices and len(past_dates) > 1
            future_has_data = future_dates and future_prices and len(future_dates) > 1

            # If BOTH sections are invalid, fall back to drawing full unsplit data
            if not past_has_data and not future_has_data:
                # Draw as if "now" is not visible (no split)
                ax.fill_between(dates_plot, 0, prices_plot, facecolor=FILL_COLOR, alpha=FILL_ALPHA, step="post", zorder=1)
                _draw_colored_price_line(
                    ax, dates_plot, prices_plot, average_price, NEAR_AVERAGE_THRESHOLD,
                    PRICE_LINE_COLOR_BELOW_AVG, PRICE_LINE_COLOR_NEAR_AVG,
                    PRICE_LINE_COLOR_ABOVE_AVG, PLOT_LINEWIDTH
                )
            else:
                # Draw dimmed fill and line for past data (use default color, no coloring)
                if past_has_data:
                    ax.fill_between(past_dates, 0, past_prices, facecolor=FILL_COLOR, alpha=FILL_ALPHA * 0.3, step="post", zorder=1)
                    # Use default price line color for past data
                    ax.step(past_dates, past_prices, PRICE_LINE_COLOR, where="post", linewidth=PLOT_LINEWIDTH, alpha=0.3, zorder=4)

                # Draw bright fill for future data
                if future_has_data:
                    ax.fill_between(future_dates, 0, future_prices, facecolor=FILL_COLOR, alpha=FILL_ALPHA, step="post", zorder=1)

                    # Draw colored segments for future data with gradient effect
                    _draw_colored_price_line(
                        ax, future_dates, future_prices, average_price, NEAR_AVERAGE_THRESHOLD,
                        PRICE_LINE_COLOR_BELOW_AVG, PRICE_LINE_COLOR_NEAR_AVG,
                        PRICE_LINE_COLOR_ABOVE_AVG, PLOT_LINEWIDTH
                    )
        else:
            # "Now" marker is not visible - draw fully bright colored line and fill
            ax.fill_between(dates_plot, 0, prices_plot, facecolor=FILL_COLOR, alpha=FILL_ALPHA, step="post", zorder=1)

            # Draw colored segments with gradient effect
            _draw_colored_price_line(
                ax, dates_plot, prices_plot, average_price, NEAR_AVERAGE_THRESHOLD,
                PRICE_LINE_COLOR_BELOW_AVG, PRICE_LINE_COLOR_NEAR_AVG,
                PRICE_LINE_COLOR_ABOVE_AVG, PLOT_LINEWIDTH
            )

        # Draw "now" line on top (always drawn)
        ax.axvline(now_local, color=NOWLINE_COLOR, alpha=NOWLINE_ALPHA, linestyle="-", zorder=5)
    else:
        # Original single-color rendering (when COLOR_PRICE_LINE_BY_AVERAGE is disabled)
        if now_is_visible:
            # Split the data into past (dimmed) and future (bright) sections
            past_dates, past_prices, future_dates, future_prices = _split_past_future_data(
                dates_plot, prices_plot, now_local
            )

            # Check if split produced valid sections
            past_has_data = past_dates and past_prices and len(past_dates) > 1
            future_has_data = future_dates and future_prices and len(future_dates) > 1

            # If BOTH sections are invalid, fall back to drawing full unsplit data
            if not past_has_data and not future_has_data:
                # Draw as if "now" is not visible (no split)
                ax.fill_between(dates_plot, 0, prices_plot, facecolor=FILL_COLOR, alpha=FILL_ALPHA, step="post", zorder=1)
                ax.step(dates_plot, prices_plot, PRICE_LINE_COLOR, where="post", linewidth=PLOT_LINEWIDTH, zorder=4)
            else:
                # Draw dimmed line and fill for past data
                if past_has_data:
                    ax.fill_between(past_dates, 0, past_prices, facecolor=FILL_COLOR, alpha=FILL_ALPHA * 0.3, step="post", zorder=1)
                    ax.step(past_dates, past_prices, PRICE_LINE_COLOR, where="post", linewidth=PLOT_LINEWIDTH, alpha=0.3, zorder=4)

                # Draw bright line and fill for future data
                if future_has_data:
                    ax.fill_between(future_dates, 0, future_prices, facecolor=FILL_COLOR, alpha=FILL_ALPHA, step="post", zorder=1)
                    ax.step(future_dates, future_prices, PRICE_LINE_COLOR, where="post", linewidth=PLOT_LINEWIDTH, zorder=4)

            # Draw "now" line on top
            ax.axvline(now_local, color=NOWLINE_COLOR, alpha=NOWLINE_ALPHA, linestyle="-", zorder=5)
        else:
            # "Now" marker is not visible - draw fully bright line and fill
            ax.fill_between(dates_plot, 0, prices_plot, facecolor=FILL_COLOR, alpha=FILL_ALPHA, step="post", zorder=1)
            ax.step(dates_plot, prices_plot, PRICE_LINE_COLOR, where="post", linewidth=PLOT_LINEWIDTH, zorder=4)
            # Still draw the now line (it will be outside visible range but matplotlib handles this)
            ax.axvline(now_local, color=NOWLINE_COLOR, alpha=NOWLINE_ALPHA, linestyle="-", zorder=5)

    # Draw glowing point at intersection of now line and price line
    # This applies regardless of where the current price label is shown (except when off)
    # The glow effect is always rendered to highlight the current price on the graph
    if LABEL_CURRENT_OPT != LABEL_CURRENT_OFF and now_is_visible and idx < len(prices_raw):
        current_price = prices_raw[idx]
        # Draw multiple overlapping circles with decreasing alpha for glow effect
        for size_factor, alpha_factor in [(3.0, 0.15), (2.0, 0.3), (1.0, 0.8)]:
            ax.plot(now_local, current_price, 'o',
                   color=NOWLINE_COLOR,
                   markersize=8 * size_factor,
                   alpha=NOWLINE_ALPHA * alpha_factor,
                   zorder=5)

    # Calculate price range early for use in label offsets
    y_min = min(visible_prices)
    y_max = max(visible_prices)
    price_range = y_max - y_min

    # Determine which data points to label (min, max, current) based on visible data
    chosen = set()
    min_idx = None
    max_idx = None
    current_idx = None

    if prices_raw:
        # Determine which indices to consider for min/max labels
        # If START_GRAPH_AT is "midnight" or "show_all": consider entire visible range (past and future)
        # If "current_hour": only consider future prices (from current time onwards)
        if START_GRAPH_AT_OPT in (START_GRAPH_AT_MIDNIGHT, START_GRAPH_AT_SHOW_ALL):
            candidate_indices = visible_indices
        else:  # START_GRAPH_AT_CURRENT_HOUR
            # Only future prices: at or after the current time
            # Note: For labels on the plot, we use strict > comparison
            candidate_indices = [i for i in visible_indices if dates_raw[i] > now_local]

        # Find indices of min and max prices among candidates
        min_idx = min(candidate_indices, key=lambda i: prices_raw[i]) if candidate_indices else None
        max_idx = max(candidate_indices, key=lambda i: prices_raw[i]) if candidate_indices else None
        current_idx = idx if idx in visible_indices else None

        # Build set of indices to label, avoiding duplicates
        if LABEL_CURRENT_OPT in (LABEL_CURRENT_ON_IN_GRAPH, LABEL_CURRENT_ON_IN_GRAPH_NO_PRICE) and current_idx is not None:
            chosen.add(current_idx)
            # Don't label min/max if they coincide with current
            if LABEL_MIN_OPT != LABEL_MIN_OFF and min_idx is not None and min_idx != current_idx:
                chosen.add(min_idx)
            if LABEL_MAX_OPT != LABEL_MAX_OFF and max_idx is not None and max_idx != current_idx:
                chosen.add(max_idx)
        else:
            if LABEL_MIN_OPT != LABEL_MIN_OFF and min_idx is not None:
                chosen.add(min_idx)
            if LABEL_MAX_OPT != LABEL_MAX_OFF and max_idx is not None:
                chosen.add(max_idx)

    # Pre-calculate label settings once to avoid repeated calculations
    label_effects = [pe.withStroke(linewidth=2, foreground=BACKGROUND_COLOR)] if LABEL_STROKE else None
    price_multiplier = 100 if USE_CENTS_OPT else 1
    decimals = PRICE_DECIMALS_OPT
    currency_label = f" {currency}" if (LABEL_SHOW_CURRENCY_OPT and currency) else ""

    # Draw labels for chosen data points (min, max, current)
    for i in sorted(chosen):
        # Skip current label here if it will be drawn in the header
        # (current_idx is only in chosen if LABEL_CURRENT_OPT in (LABEL_CURRENT_ON_IN_GRAPH, LABEL_CURRENT_ON_IN_GRAPH_NO_PRICE))
        # So this check is technically redundant, but kept for clarity
        if i == current_idx and LABEL_CURRENT_OPT not in (LABEL_CURRENT_ON_IN_GRAPH, LABEL_CURRENT_ON_IN_GRAPH_NO_PRICE):
            continue

        # Classify this point to determine styling
        is_min = (min_idx is not None and i == min_idx)
        is_max = (max_idx is not None and i == max_idx)
        is_current = (current_idx is not None and i == current_idx)

        # Determine if price should be shown (can be disabled for min/max with no_price option or for current with no_price option)
        show_price_min = is_min and LABEL_MIN_OPT == LABEL_MIN_ON_NO_PRICE
        show_price_max = is_max and LABEL_MAX_OPT == LABEL_MAX_ON_NO_PRICE
        show_price = not (show_price_min or show_price_max) and not (is_current and LABEL_CURRENT_OPT == LABEL_CURRENT_ON_IN_GRAPH_NO_PRICE)

        # Build label text: price + time or just time
        # For current price, show minutes; for min/max, show only hour
        time_str = now_local.strftime('%H:%M') if is_current else dates_raw[i].strftime('%H')
        if show_price:
            price_display = prices_raw[i] * price_multiplier
            label_text = f"{price_display:.{decimals}f}{currency_label}\n{label_at} {time_str}"
        else:
            label_text = time_str

        # Set vertical alignment:
        # - Current labels always use "bottom" (above point) for in-graph labels
        # - Max labels use "top" (below point) if LABEL_MAX_BELOW_POINT or current label is not shown in graph
        # - Min labels always use "bottom" (above point)
        if is_current:
            vertical_align = "bottom"
        elif is_max and (LABEL_MAX_BELOW_POINT_OPT or LABEL_CURRENT_OPT not in (LABEL_CURRENT_ON_IN_GRAPH, LABEL_CURRENT_ON_IN_GRAPH_NO_PRICE)):
            vertical_align = "top"
        else:
            vertical_align = "bottom"

        # Determine label color: use colored labels if enabled
        if LABEL_USE_COLORS_OPT:
            if is_min:
                label_color = LABEL_COLOR_MIN
            elif is_max:
                label_color = LABEL_COLOR_MAX
            else:
                label_color = LABEL_COLOR
        else:
            label_color = LABEL_COLOR

        # Calculate label offset to move label away from point
        # Use a small percentage of the price range for offset
        # Use larger offset for labels below points (top alignment)
        label_offset_up = price_range * 0.02  # 2% of price range for labels above points
        label_offset_down = price_range * 0.035  # 3.5% of price range for labels below points
        # Apply offset based on vertical alignment
        label_y_pos = prices_raw[i] + label_offset_up if vertical_align == "bottom" else prices_raw[i] - label_offset_down

        # For current price, use exact current time position; for min/max, use data point time
        label_x_pos = now_local if is_current else dates_raw[i]

        ax.text(
            label_x_pos,
            label_y_pos,
            label_text,
            fontsize=LABEL_FONT_SIZE_OPT,
            va=vertical_align,
            ha="center",
            color=label_color,
            fontweight=LABEL_FONT_WEIGHT_OPT,
            zorder=7,
            path_effects=label_effects,
        )

        # Draw point at the data point for in-graph labels
        # Skip drawing solid point for current price since glowing point is drawn separately
        if not is_current:
            # Determine if this point is in the past for dimming
            is_past = dates_raw[i] <= now_local

            # For min/max, determine color based on whether COLOR_PRICE_LINE_BY_AVERAGE is enabled
            # Only use colored price line logic for future points
            if COLOR_PRICE_LINE_BY_AVERAGE_OPT and calc_prices and len(calc_prices) > 0 and not is_past:
                # Calculate average price from calculation data (filtered based on display options)
                average_price = sum(calc_prices) / len(calc_prices)
                # Use helper function for consistent color calculation
                point_color_rgb = _get_price_color(prices_raw[i], average_price, NEAR_AVERAGE_THRESHOLD,
                                                    PRICE_LINE_COLOR_BELOW_AVG, PRICE_LINE_COLOR_NEAR_AVG,
                                                    PRICE_LINE_COLOR_ABOVE_AVG)
                # Convert RGB tuple to hex for matplotlib plot
                import matplotlib.colors as mcolors
                point_color = mcolors.to_hex(point_color_rgb)
            else:
                # Use default price line color when color-by-average is disabled or point is in past
                point_color = PRICE_LINE_COLOR

            # Draw the point at the data point (same size and transparency as inner ring of glowing point)
            # Z-order 5 ensures labels (z-order 7) appear above the points
            # Dim the point if it's in the past (apply additional 0.3 alpha factor, matching price line dimming)
            point_alpha = NOWLINE_ALPHA * 0.8
            if is_past:
                point_alpha *= 0.3

            ax.plot(dates_raw[i], prices_raw[i], 'o',
                   color=point_color,
                   markersize=8,
                   alpha=point_alpha,
                   zorder=5)

    # Draw current price label at fixed position (centered at top above graph) if enabled
    if current_idx is not None and LABEL_CURRENT_OPT in (LABEL_CURRENT_ON, LABEL_CURRENT_ON_CURRENT_PRICE_ONLY):
        price_display = prices_raw[current_idx] * price_multiplier
        now_time = now_local.strftime("%H:%M")
        ax_pos = ax.get_position()
        # Center the label horizontally within the graph area
        label_x = (ax_pos.x0 + ax_pos.x1) / 2
        # Padding now counts from bottom of text (va="bottom")
        label_y = 1.0 - LABEL_CURRENT_IN_HEADER_PADDING_OPT

        # Build header text - show additional info if mode is "on", only current price if "on_current_price_only"
        if LABEL_CURRENT_OPT == LABEL_CURRENT_ON and calc_prices and len(calc_prices) > 0:
            # Calculate average price from calculation data (filtered based on display options)
            average_price = sum(calc_prices) / len(calc_prices)
            avg_display = average_price * price_multiplier

            # Calculate percentage to average (never include '+' sign)
            current_price = prices_raw[current_idx]
            pct_to_avg = ((current_price / average_price) * 100)
            pct_rounded = round(pct_to_avg)
            pct_str = f"{pct_rounded}%" if pct_rounded >= 0 else f"{pct_rounded}%"

            # Build header as segments to allow different font weights and sizes for separators
            header_segments = [
                (f"{price_display:.{decimals}f}{currency_label} {label_at} {now_time}", LABEL_CURRENT_IN_HEADER_FONT_WEIGHT_OPT, LABEL_FONT_SIZE_OPT),
                (" │ ", "normal", LABEL_FONT_SIZE_OPT - 1),
                (f"{label_avg} {avg_display:.{decimals}f}{currency_label}", LABEL_CURRENT_IN_HEADER_FONT_WEIGHT_OPT, LABEL_FONT_SIZE_OPT),
                (" • ", "normal", LABEL_FONT_SIZE_OPT - 1),
                (pct_str, LABEL_CURRENT_IN_HEADER_FONT_WEIGHT_OPT, LABEL_FONT_SIZE_OPT),
            ]
        else:
            header_segments = [
                (f"{price_display:.{decimals}f}{currency_label} {label_at} {now_time}", LABEL_CURRENT_IN_HEADER_FONT_WEIGHT_OPT, LABEL_FONT_SIZE_OPT),
            ]

        # Calculate full header width to center properly
        full_header_text = "".join([seg[0] for seg in header_segments])
        temp_text = fig.text(label_x, label_y, full_header_text,
                            fontsize=LABEL_FONT_SIZE_OPT,
                            color=LABEL_COLOR,
                            fontweight=LABEL_CURRENT_IN_HEADER_FONT_WEIGHT_OPT,
                            va="bottom", ha="center", zorder=7,
                            path_effects=label_effects)
        # Get bounding box to calculate width
        bbox = temp_text.get_window_extent(renderer=fig.canvas.get_renderer())
        temp_text.remove()

        # Transform bbox to figure coordinates
        bbox_fig = bbox.transformed(fig.transFigure.inverted())
        total_width = bbox_fig.width

        # Calculate starting x position (left edge of centered text)
        start_x = label_x - (total_width / 2)

        # Draw each segment with its own font weight and size
        current_x = start_x
        for segment_text, font_weight, font_size in header_segments:
            text_obj = fig.text(
                current_x,
                label_y,
                segment_text,
                fontsize=font_size,
                color=LABEL_COLOR,
                fontweight=font_weight,
                va="bottom",
                ha="left",
                zorder=7,
                path_effects=label_effects,
            )
            # Get width of this segment to position next segment
            seg_bbox = text_obj.get_window_extent(renderer=fig.canvas.get_renderer())
            seg_bbox_fig = seg_bbox.transformed(fig.transFigure.inverted())
            current_x += seg_bbox_fig.width

    # Set X-axis range and Y-axis limits based on visible data
    ax.set_xlim((start_hour, end_hour))
    # Add padding proportional to the price range to prevent data from touching the edges
    # Use 5% padding at both bottom and top
    pad_low = max(price_range * 0.05, 0.01)  # At least 0.01 to handle very small ranges
    pad_high = max(price_range * 0.05, 0.01)  # At least 0.01 to handle very small ranges
    ax.set_ylim((y_min - pad_low, y_max + pad_high))

    # Draw average price line if enabled (at same z-order as horizontal grid lines)
    # Average is calculated from calculation data (filtered based on display options)
    if SHOW_AVERAGE_PRICE_LINE_OPT and average_price is not None:
        ax.axhline(average_price, color=NOWLINE_COLOR, alpha=GRID_ALPHA, linestyle=":", linewidth=1, zorder=2)

    # Calculate Y-axis tick min/max values
    # Key difference: For labels we use strict future (>), but for ticks we use current hour onwards (>=)
    # When starting at current hour, ticks should only consider future prices (from current hour onwards)
    if START_GRAPH_AT_OPT in (START_GRAPH_AT_MIDNIGHT, START_GRAPH_AT_SHOW_ALL):
        # Use all visible prices for ticks (past and future)
        y_min_tick = y_min
        y_max_tick = y_max
    elif candidate_indices:
        # Use only future prices for ticks (from current hour onwards for hourly data)
        # This ensures ticks reflect only what's ahead, not what's already past
        now_hour_start = now_local.replace(minute=0, second=0, microsecond=0)
        future_indices = [i for i in visible_indices if dates_raw[i] >= now_hour_start]

        if future_indices:
            future_prices = [prices_raw[i] for i in future_indices]
            y_min_tick = min(future_prices)
            y_max_tick = max(future_prices)
        else:
            # Fallback to all visible prices if no future prices
            y_min_tick = y_min
            y_max_tick = y_max
    else:
        # Fallback to all visible prices if no candidates
        y_min_tick = y_min
        y_max_tick = y_max

    # Configure Y-axis formatting and ticks (only when Y axis is visible)
    if show_y_axis_visible:
        # Format Y-axis labels: multiply by 100 if showing cents
        decimals_axis = PRICE_DECIMALS_OPT
        if USE_CENTS_OPT:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, pos: f"{v * 100:.{decimals_axis}f}"))
        else:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, pos: f"{v:.{decimals_axis}f}"))

        # Apply tick count if configured
        if Y_TICK_COUNT_OPT:
            try:
                if Y_TICK_COUNT_OPT == 1:
                    # Show average from calculation data (consistent with average price line)
                    if calc_prices and len(calc_prices) > 0:
                        y_avg = sum(calc_prices) / len(calc_prices)
                    elif prices_raw and len(prices_raw) > 0:
                        y_avg = sum(prices_raw) / len(prices_raw)
                    else:
                        y_avg = 0
                    ax.yaxis.set_major_locator(mticker.FixedLocator([y_avg]))
                    if Y_TICK_USE_COLORS_OPT:
                        for tick_label in ax.yaxis.get_ticklabels():
                            tick_label.set_color(LABEL_COLOR_AVG)

                elif Y_TICK_COUNT_OPT == 2:
                    # Show min and max (future only if starting at current hour)
                    ax.yaxis.set_major_locator(mticker.FixedLocator([y_min_tick, y_max_tick]))
                    if Y_TICK_USE_COLORS_OPT:
                        tick_labels = ax.yaxis.get_ticklabels()
                        if len(tick_labels) >= 2:
                            tick_labels[0].set_color(LABEL_COLOR_MIN)
                            tick_labels[1].set_color(LABEL_COLOR_MAX)

                elif Y_TICK_COUNT_OPT == 3:
                    # Show min, max, and average from calculation data (consistent with average price line)
                    if calc_prices and len(calc_prices) > 0:
                        y_avg = sum(calc_prices) / len(calc_prices)
                    elif prices_raw and len(prices_raw) > 0:
                        y_avg = sum(prices_raw) / len(prices_raw)
                    else:
                        y_avg = (y_min_tick + y_max_tick) / 2
                    ax.yaxis.set_major_locator(mticker.FixedLocator([y_min_tick, y_avg, y_max_tick]))
                    if Y_TICK_USE_COLORS_OPT:
                        tick_labels = ax.yaxis.get_ticklabels()
                        if len(tick_labels) >= 3:
                            tick_labels[0].set_color(LABEL_COLOR_MIN)
                            tick_labels[1].set_color(LABEL_COLOR_AVG)
                            tick_labels[2].set_color(LABEL_COLOR_MAX)

                elif Y_TICK_COUNT_OPT >= 4:
                    # Show min, max, and evenly distributed ticks between them
                    # Total ticks = Y_TICK_COUNT_OPT, including min and max
                    # Interior ticks = Y_TICK_COUNT_OPT - 2
                    num_interior = Y_TICK_COUNT_OPT - 2
                    if num_interior > 0:
                        step = (y_max_tick - y_min_tick) / (num_interior + 1)
                        tick_positions = [y_min_tick] + [y_min_tick + step * (i + 1) for i in range(num_interior)] + [y_max_tick]
                    else:
                        # If Y_TICK_COUNT_OPT is exactly 4, just show min and max with 2 evenly spaced ticks
                        tick_positions = [y_min_tick, y_min_tick + (y_max_tick - y_min_tick) / 3, y_min_tick + 2 * (y_max_tick - y_min_tick) / 3, y_max_tick]
                    ax.yaxis.set_major_locator(mticker.FixedLocator(tick_positions))
                    if Y_TICK_USE_COLORS_OPT:
                        tick_labels = ax.yaxis.get_ticklabels()
                        if len(tick_labels) >= 2:
                            # Color the first (min) and last (max) tick labels
                            tick_labels[0].set_color(LABEL_COLOR_MIN)
                            tick_labels[-1].set_color(LABEL_COLOR_MAX)
            except Exception:
                # Silently ignore errors in tick configuration (e.g., division by zero)
                pass

    # Draw X-axis tick lines and labels manually
    # Helper function to round datetime to nearest hour (for 15-min pricing)
    def _round_to_nearest_hour(dt):
        """Round datetime to nearest hour (>= 30 min rounds up)."""
        rounded = dt.replace(minute=0, second=0, microsecond=0)
        if dt.minute >= 30:
            rounded += datetime.timedelta(hours=1)
        return rounded

    # Check if we have future cheap periods that should be shown on x-axis
    future_cheap_periods = []
    has_cheap_periods = (CHEAP_PRICE_POINTS_OPT > 0 or CHEAP_PRICE_THRESHOLD_OPT > 0) and 'cheap_indices_all_days' in locals()

    if has_cheap_periods and CHEAP_PERIODS_ON_X_AXIS_OPT != CHEAP_PERIODS_ON_X_AXIS_OFF:
        # Filter for future cheap periods only
        for cheap_idx in cheap_indices_all_days:
            period_start = dates_raw[cheap_idx]
            period_end = period_start + period_duration

            # Only include future periods (start is after now)
            if period_start > now_local and period_start <= end_hour and period_end >= start_hour:
                future_cheap_periods.append((period_start, period_end, cheap_idx))

        # Sort by start time
        future_cheap_periods.sort(key=lambda x: x[0])

    # Determine if we're using 15-minute pricing (step_minutes < 60)
    is_fifteen_min_pricing = step_minutes < 60

    # If there are future cheap periods, group them into continuous ranges
    # and track gap boundary times for intermediate labels
    cheap_ranges = []
    gap_start_times = []  # Track where gaps (non-cheap periods) start (when cheap resumes)
    gap_end_times = []    # Track where gaps start (when cheap ends before gap)
    if future_cheap_periods:
        current_range_start = future_cheap_periods[0][0]
        current_range_end = future_cheap_periods[0][1]

        # Treat gaps of 1 hour or less as continuous (for both 15 min and 60 min pricing)
        gap_threshold_seconds = 3600

        for i in range(1, len(future_cheap_periods)):
            period_start, period_end, _ = future_cheap_periods[i]

            # Check if this period is continuous with the current range
            if (period_start - current_range_end).total_seconds() < gap_threshold_seconds:
                # There's a gap, but we're merging the ranges for display
                # Track both the end of cheap period before gap and start after gap
                if (period_start - current_range_end).total_seconds() > 0:
                    gap_end_times.append(current_range_end)
                    gap_start_times.append(period_start)
                # Extend the current range
                current_range_end = period_end
            else:
                # Save the current range and start a new one
                cheap_ranges.append((current_range_start, current_range_end))
                current_range_start = period_start
                current_range_end = period_end

        # Don't forget the last range
        cheap_ranges.append((current_range_start, current_range_end))

    # Generate regular tick times at configured intervals
    regular_ticks = []
    t = start_hour
    while t <= end_hour:
        regular_ticks.append(t)
        t += datetime.timedelta(hours=X_TICK_STEP_HOURS_OPT)

    # Build final tick list based on configuration
    tick_times = []
    tick_colors = []
    # Boundary threshold: use X_TICK_STEP_HOURS if CHEAP_PERIOD_BOUNDARY_HOURS is 0
    boundary_threshold_seconds = (CHEAP_PERIOD_BOUNDARY_HOURS if CHEAP_PERIOD_BOUNDARY_HOURS > 0 else X_TICK_STEP_HOURS_OPT) * 3600

    # Determine if we should show cheap period boundaries on x-axis
    show_cheap_boundaries = cheap_ranges and CHEAP_PERIODS_ON_X_AXIS_OPT != CHEAP_PERIODS_ON_X_AXIS_OFF

    # Helper functions for tick time processing
    def _get_tick_time(dt):
        """Get tick time: rounded to nearest hour for 15-min pricing, exact otherwise."""
        return _round_to_nearest_hour(dt) if is_fifteen_min_pricing else dt

    def _is_in_cheap_range(tick):
        """Check if tick falls within any merged cheap period range."""
        return any(range_start <= tick <= range_end for range_start, range_end in cheap_ranges)

    def _add_gap_boundary_ticks(gap_times, range_start, range_end, cheap_tick_times):
        """Add gap boundary ticks within a range if not already present."""
        for gap_time in gap_times:
            if range_start <= gap_time <= range_end:
                gap_tick = _get_tick_time(gap_time)
                if gap_tick not in cheap_tick_times:
                    cheap_tick_times.append(gap_tick)

    def _draw_x_label(ax, tick_time, y_offset, label_color, label_effects, fontweight="normal"):
        """Draw x-axis label at specified position with given styling."""
        ax.text(
            tick_time,
            -y_offset,
            tick_time.strftime("%H"),
            transform=ax.get_xaxis_transform(),
            rotation=0,
            ha="center",
            va="top",
            fontsize=LABEL_FONT_SIZE_OPT,
            fontweight=fontweight,
            color=label_color,
            clip_on=False,
            zorder=6,
            path_effects=label_effects,
        )

    # Collect cheap period boundary and gap times
    cheap_tick_times = []
    if show_cheap_boundaries:
        for idx, (range_start, range_end) in enumerate(cheap_ranges):
            tick_start = _get_tick_time(range_start)
            tick_end = _get_tick_time(range_end)

            # Always add start label (filtering for row placement happens later)
            cheap_tick_times.append(tick_start)

            # Add gap boundary labels within this range (both gap ends and gap starts)
            _add_gap_boundary_ticks(gap_end_times, range_start, range_end, cheap_tick_times)
            _add_gap_boundary_ticks(gap_start_times, range_start, range_end, cheap_tick_times)

            # Add end label if it differs from start AND period is long enough
            # (at least x_tick_step_hours) to warrant showing both start and end
            if tick_end != tick_start:
                period_length_seconds = (range_end - range_start).total_seconds()
                if period_length_seconds >= boundary_threshold_seconds:
                    cheap_tick_times.append(tick_end)

    # Choose tick generation strategy based on configuration
    if CHEAP_PERIODS_ON_X_AXIS_OPT in (CHEAP_PERIODS_ON_X_AXIS_ON, CHEAP_PERIODS_ON_X_AXIS_ON_COMFY):
        # Mode 1: Show all regular ticks, add cheap period labels in separate row below (for "on_comfy")
        # or just highlight existing ticks (for "on")
        tick_times = regular_ticks
        tick_colors = [AXIS_LABEL_COLOR] * len(tick_times)
    else:
        # Mode 2 (on_compact): Show regular ticks that are not too close to boundaries, add cheap boundary labels
        tick_times = []
        tick_colors = []

        if show_cheap_boundaries:
            # Keep only regular ticks that are far enough from cheap period boundaries
            for regular_tick in regular_ticks:
                is_far_enough = all(abs((regular_tick - ct).total_seconds()) >= boundary_threshold_seconds for ct in cheap_tick_times)

                if is_far_enough:
                    tick_times.append(regular_tick)
                    # Color if in cheap range, otherwise default color
                    if _is_in_cheap_range(regular_tick):
                        tick_colors.append(LABEL_COLOR_MIN)
                    else:
                        tick_colors.append(AXIS_LABEL_COLOR)

            # Always add cheap boundary ticks
            tick_times.extend(cheap_tick_times)
            tick_colors.extend([LABEL_COLOR_MIN] * len(cheap_tick_times))

            # Sort by time to maintain correct order
            combined = sorted(zip(tick_times, tick_colors), key=lambda x: x[0])
            tick_times, tick_colors = zip(*combined) if combined else ([], [])
            tick_times, tick_colors = list(tick_times), list(tick_colors)
        else:
            # No cheap boundaries, just use regular ticks with default color
            tick_times = regular_ticks
            tick_colors = [AXIS_LABEL_COLOR] * len(tick_times)

    ylim = ax.get_ylim()
    xlab_effects = [pe.withStroke(linewidth=2, foreground=BACKGROUND_COLOR)] if LABEL_STROKE else None

    # Check if X-axis should be shown (off = hide completely)
    show_x_axis = SHOW_X_AXIS_OPT != SHOW_X_AXIS_OFF

    # Enable X-ticks at the tick positions if configured to show tick marks
    if show_x_axis and SHOW_X_AXIS_OPT == SHOW_X_AXIS_ON_WITH_TICK_MARKS:
        ax.set_xticks(tick_times)
        ax.tick_params(axis="x", which="both", bottom=True, top=False, labelbottom=False, color=TICK_COLOR)

    # Prepare separate row mode: identify ticks in cheap ranges and filter cheap-only ticks
    matching_ticks = set()
    cheap_only_ticks = []

    if CHEAP_PERIODS_ON_X_AXIS_OPT in (CHEAP_PERIODS_ON_X_AXIS_ON, CHEAP_PERIODS_ON_X_AXIS_ON_COMFY) and show_cheap_boundaries:
        # Identify regular ticks that fall within cheap ranges (will be colored on row one)
        matching_ticks = set(tt for tt in tick_times if _is_in_cheap_range(tt))

        # For "on_comfy" mode, filter cheap boundary ticks that don't match regular ticks
        # to avoid labels too close together (second row)
        if CHEAP_PERIODS_ON_X_AXIS_OPT == CHEAP_PERIODS_ON_X_AXIS_ON_COMFY:
            sorted_cheap_ticks = sorted(ct for ct in cheap_tick_times if ct not in tick_times)

            if sorted_cheap_ticks:
                cheap_only_ticks.append(sorted_cheap_ticks[0])
                for cheap_tick in sorted_cheap_ticks[1:]:
                    if (cheap_tick - cheap_only_ticks[-1]).total_seconds() >= boundary_threshold_seconds:
                        cheap_only_ticks.append(cheap_tick)

    # Determine if second row is needed (only for "on_comfy" mode)
    need_second_row = bool(CHEAP_PERIODS_ON_X_AXIS_OPT == CHEAP_PERIODS_ON_X_AXIS_ON_COMFY and cheap_only_ticks)

    # Draw time labels (and optionally vertical grid lines) only if X-axis is shown
    if show_x_axis:
        for tt, tick_color in zip(tick_times, tick_colors):
            # Draw vertical grid lines only if show_vertical_grid is enabled
            if SHOW_VERTICAL_GRID_OPT:
                ax.vlines([tt], ymin=ylim[0], ymax=ylim[1], colors=GRID_COLOR, linewidth=1.0, alpha=GRID_ALPHA, zorder=2)

            # Determine label color: 'label_color_min' if in cheap range, otherwise use default tick color
            label_color = LABEL_COLOR_MIN if tt in matching_ticks else tick_color

            # Determine font weight: bold for boundary labels when highlighting is enabled
            # In compact mode: bold if in cheap_tick_times
            # In comfy mode: bold if in cheap_tick_times (boundary labels on row one)
            if (CHEAP_PERIOD_BOUNDARY_HIGHLIGHT_OPT and show_cheap_boundaries and
                CHEAP_PERIODS_ON_X_AXIS_OPT in (CHEAP_PERIODS_ON_X_AXIS_ON_COMPACT, CHEAP_PERIODS_ON_X_AXIS_ON_COMFY) and
                tt in cheap_tick_times):
                fontweight = "bold"
            else:
                fontweight = "normal"

            _draw_x_label(ax, tt, X_AXIS_LABEL_Y_OFFSET, label_color, xlab_effects, fontweight)

    # Handle bottom margin and optional separate row for cheap labels
    adjusted_bottom_margin = BOTTOM_MARGIN_OPT

    # If we need a second row, draw cheap-only labels below the regular ones (only if X-axis is shown)
    if show_x_axis and need_second_row:
        # Calculate offset for cheap period labels (below regular labels)
        # Scale the offset based on font size to prevent overlap with larger fonts
        # Base offset (0.05) works for font size 11-13; scale up for larger fonts
        font_scale = max(1.0, LABEL_FONT_SIZE_OPT / 12)
        cheap_label_y_offset = X_AXIS_LABEL_Y_OFFSET * 2.5 * font_scale

        # Adjust bottom margin to maintain same spacing from bottom of image
        # Use smaller multiplier for larger fonts: 0.7 for small fonts, 0.5 for large fonts
        margin_multiplier = max(0.5, 0.7 - (font_scale - 1.0) * 0.3)
        extra_offset = (cheap_label_y_offset - X_AXIS_LABEL_Y_OFFSET) * margin_multiplier
        adjusted_bottom_margin = BOTTOM_MARGIN_OPT + extra_offset

        # Draw cheap-only labels on second row
        for tt in cheap_only_ticks:
            # Make boundary labels bold in comfy mode when highlighting is enabled
            fontweight = "bold" if CHEAP_PERIOD_BOUNDARY_HIGHLIGHT_OPT else "normal"
            _draw_x_label(ax, tt, cheap_label_y_offset, LABEL_COLOR_MIN, xlab_effects, fontweight)

    # Finalize plot layout and save
    ax.margins(x=0)
    fig.subplots_adjust(bottom=adjusted_bottom_margin, left=LEFT_MARGIN_OPT, right=1-LEFT_MARGIN_OPT)

    # Use temporary file to prevent corrupting the existing image on render failure
    import tempfile
    import os
    temp_fd = None
    temp_path = None

    try:
        # Create temporary file in same directory as output to ensure same filesystem
        # This allows atomic rename operation
        out_dir = os.path.dirname(out_path)
        temp_fd, temp_path = tempfile.mkstemp(suffix='.png', dir=out_dir)
        os.close(temp_fd)  # Close the file descriptor; savefig will open it

        # Save to temporary file with correct figure background to avoid white edges
        fig.savefig(temp_path, facecolor=fig.get_facecolor())

        # Only replace the actual output file if render succeeded
        # This is atomic on most filesystems, preventing partial/corrupt images
        os.replace(temp_path, out_path)
        temp_path = None  # Mark as successfully moved

    except Exception as err:
        # If rendering fails, preserve the existing output file
        # Log the error but don't raise - gracefully fail without corrupting the image
        import logging
        _LOGGER = logging.getLogger(__name__)
        _LOGGER.error("Failed to render graph to %s: %s", out_path, err, exc_info=True)

    finally:
        # Clean up temporary file if it still exists (render failed)
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass

        # Clean up matplotlib objects to prevent memory leaks
        ax.clear()
        plt.close(fig)
        plt.close("all")
