"""Rendering logic for Tibber price graphs using matplotlib."""
import datetime

from dateutil import tz
import matplotlib
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Import default constants from const.py for fallback values
from .const import (
    DEFAULT_THEME as THEME,
    DEFAULT_TRANSPARENT_BACKGROUND as TRANSPARENT_BACKGROUND,
    DEFAULT_CANVAS_WIDTH as CANVAS_WIDTH,
    DEFAULT_CANVAS_HEIGHT as CANVAS_HEIGHT,
    DEFAULT_FORCE_FIXED_SIZE as FORCE_FIXED_SIZE,
    DEFAULT_BOTTOM_MARGIN as BOTTOM_MARGIN,
    DEFAULT_LEFT_MARGIN as LEFT_MARGIN,
    DEFAULT_X_AXIS_LABEL_Y_OFFSET as X_AXIS_LABEL_Y_OFFSET,
    DEFAULT_SHOW_X_TICKS as SHOW_X_TICKS,
    DEFAULT_START_GRAPH_AT as START_GRAPH_AT,
    DEFAULT_X_TICK_STEP_HOURS as X_TICK_STEP_HOURS,
    DEFAULT_HOURS_TO_SHOW as HOURS_TO_SHOW,
    DEFAULT_SHOW_VERTICAL_GRID as SHOW_VERTICAL_GRID,
    DEFAULT_SHOW_Y_AXIS as SHOW_Y_AXIS,
    DEFAULT_SHOW_Y_AXIS_TICKS as SHOW_Y_AXIS_TICKS,
    DEFAULT_SHOW_HORIZONTAL_GRID as SHOW_HORIZONTAL_GRID,
    DEFAULT_SHOW_AVERAGE_PRICE_LINE as SHOW_AVERAGE_PRICE_LINE,
    DEFAULT_CHEAP_PRICE_POINTS as CHEAP_PRICE_POINTS,
    DEFAULT_Y_AXIS_LABEL_ROTATION_DEG as Y_AXIS_LABEL_ROTATION_DEG,
    DEFAULT_Y_AXIS_LABEL_VERTICAL_ANCHOR as Y_AXIS_LABEL_VERTICAL_ANCHOR,
    DEFAULT_Y_AXIS_SIDE as Y_AXIS_SIDE,
    DEFAULT_Y_TICK_COUNT as Y_TICK_COUNT,
    DEFAULT_Y_TICK_USE_COLORS as Y_TICK_USE_COLORS,
    DEFAULT_USE_CENTS as USE_CENTS,
    DEFAULT_CURRENCY_OVERRIDE as CURRENCY_OVERRIDE,
    DEFAULT_LABEL_CURRENT as LABEL_CURRENT,
    DEFAULT_LABEL_CURRENT_AT_TOP as LABEL_CURRENT_AT_TOP,
    DEFAULT_LABEL_CURRENT_AT_TOP_FONT_WEIGHT as LABEL_CURRENT_AT_TOP_FONT_WEIGHT,
    DEFAULT_LABEL_CURRENT_AT_TOP_PADDING as LABEL_CURRENT_AT_TOP_PADDING,
    DEFAULT_LABEL_FONT_SIZE as LABEL_FONT_SIZE,
    DEFAULT_LABEL_FONT_WEIGHT as LABEL_FONT_WEIGHT,
    DEFAULT_LABEL_MAX as LABEL_MAX,
    DEFAULT_LABEL_MAX_BELOW_POINT as LABEL_MAX_BELOW_POINT,
    DEFAULT_LABEL_MIN as LABEL_MIN,
    DEFAULT_LABEL_MINMAX_SHOW_PRICE as LABEL_MINMAX_SHOW_PRICE,
    DEFAULT_LABEL_SHOW_CURRENCY as LABEL_SHOW_CURRENCY,
    DEFAULT_LABEL_USE_COLORS as LABEL_USE_COLORS,
    DEFAULT_PRICE_DECIMALS as PRICE_DECIMALS,
    DEFAULT_COLOR_PRICE_LINE_BY_AVERAGE as COLOR_PRICE_LINE_BY_AVERAGE,
    DEFAULT_NEAR_AVERAGE_THRESHOLD as NEAR_AVERAGE_THRESHOLD,
    START_GRAPH_AT_MIDNIGHT,
    START_GRAPH_AT_CURRENT_HOUR,
    START_GRAPH_AT_SHOW_ALL,
)

# Import theme color constants from defaults.py for dynamic theme selection
from .defaults import (
    LIGHT_BACKGROUND_COLOR,
    LIGHT_CHEAP_PRICE_COLOR,
    LIGHT_FILL_ALPHA,
    LIGHT_FILL_COLOR,
    LIGHT_GRID_ALPHA,
    LIGHT_GRID_COLOR,
    LIGHT_LABEL_COLOR,
    LIGHT_NOWLINE_ALPHA,
    LIGHT_NOWLINE_COLOR,
    LIGHT_PLOT_LINEWIDTH,
    LIGHT_PRICE_LINE_COLOR,
    LIGHT_SPINE_COLOR,
    LIGHT_STYLE_NAME,
    LIGHT_TICK_COLOR,
    LIGHT_TICKLINE_COLOR,
    LIGHT_AXIS_LABEL_COLOR,
    LIGHT_LABEL_STROKE,
    LIGHT_LABEL_COLOR_MIN,
    LIGHT_LABEL_COLOR_MAX,
    LIGHT_LABEL_COLOR_AVG,
    DARK_BACKGROUND_COLOR,
    DARK_CHEAP_PRICE_COLOR,
    DARK_FILL_ALPHA,
    DARK_FILL_COLOR,
    DARK_GRID_ALPHA,
    DARK_GRID_COLOR,
    DARK_LABEL_COLOR,
    DARK_NOWLINE_ALPHA,
    DARK_NOWLINE_COLOR,
    DARK_PLOT_LINEWIDTH,
    DARK_PRICE_LINE_COLOR,
    DARK_SPINE_COLOR,
    DARK_STYLE_NAME,
    DARK_TICK_COLOR,
    DARK_TICKLINE_COLOR,
    DARK_AXIS_LABEL_COLOR,
    DARK_LABEL_STROKE,
    DARK_LABEL_COLOR_MIN,
    DARK_LABEL_COLOR_MAX,
    DARK_LABEL_COLOR_AVG,
    LIGHT_PRICE_LINE_COLOR_ABOVE_AVG,
    LIGHT_PRICE_LINE_COLOR_BELOW_AVG,
    LIGHT_PRICE_LINE_COLOR_NEAR_AVG,
    DARK_PRICE_LINE_COLOR_ABOVE_AVG,
    DARK_PRICE_LINE_COLOR_BELOW_AVG,
    DARK_PRICE_LINE_COLOR_NEAR_AVG,
)

# Matplotlib heavy imports: import once at module load to reduce per-render overhead
matplotlib.use("Agg")

# Apply global rc settings once
plt.rcdefaults()
plt.rcParams.update({'font.size': 12})

# Reuse local timezone object
LOCAL_TZ = tz.tzlocal()


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
):
    """Render and save the matplotlib price chart.

    Args:
        width: Canvas width in pixels
        height: Canvas height in pixels
        dates_plot: List of datetime objects for plotting (includes extra point for step plot)
        prices_plot: List of prices for plotting (includes extra point for step plot)
        dates_raw: Original list of datetime objects (raw data)
        prices_raw: Original list of prices (raw data)
        now_local: Current local time as datetime
        idx: Index of current price in raw data
        currency: Currency code string (e.g., "EUR", "SEK", "öre")
        out_path: Output file path for the rendered image
        render_options: Optional dict of rendering options to override defaults.py values
    """
    # Matplotlib imports and rc settings are prepared at module import to
    # minimize per-render overhead.
    # Use the module-level plt, mticker, pe that were imported earlier.

    # Apply render options if provided, otherwise use global config values
    if render_options is None:
        render_options = {}

    # Get option with fallback to global config
    def get_opt(key, global_var):
        return render_options.get(key, global_var)

    # Extract all configurable options from render_options (or use defaults)
    # General settings
    THEME_OPT = get_opt("theme", THEME)
    CANVAS_WIDTH_OPT = get_opt("canvas_width", CANVAS_WIDTH)
    CANVAS_HEIGHT_OPT = get_opt("canvas_height", CANVAS_HEIGHT)
    FORCE_FIXED_SIZE_OPT = get_opt("force_fixed_size", FORCE_FIXED_SIZE)
    BOTTOM_MARGIN_OPT = get_opt("bottom_margin", BOTTOM_MARGIN)
    LEFT_MARGIN_OPT = get_opt("left_margin", LEFT_MARGIN)
    # X-axis settings
    SHOW_X_TICKS_OPT = get_opt("show_x_ticks", SHOW_X_TICKS)
    START_GRAPH_AT_OPT = get_opt("start_graph_at", START_GRAPH_AT)
    X_TICK_STEP_HOURS_OPT = get_opt("x_tick_step_hours", X_TICK_STEP_HOURS)
    HOURS_TO_SHOW_OPT = get_opt("hours_to_show", HOURS_TO_SHOW)
    SHOW_VERTICAL_GRID_OPT = get_opt("show_vertical_grid", SHOW_VERTICAL_GRID)
    # Y-axis settings
    SHOW_Y_AXIS_OPT = get_opt("show_y_axis", SHOW_Y_AXIS)
    SHOW_Y_AXIS_TICKS_OPT = get_opt("show_y_axis_ticks", SHOW_Y_AXIS_TICKS)
    SHOW_HORIZONTAL_GRID_OPT = get_opt("show_horizontal_grid", SHOW_HORIZONTAL_GRID)
    SHOW_AVERAGE_PRICE_LINE_OPT = get_opt("show_average_price_line", SHOW_AVERAGE_PRICE_LINE)
    CHEAP_PRICE_POINTS_OPT = get_opt("cheap_price_points", CHEAP_PRICE_POINTS)
    Y_AXIS_LABEL_ROTATION_DEG_OPT = get_opt("y_axis_label_rotation_deg", Y_AXIS_LABEL_ROTATION_DEG)
    Y_AXIS_LABEL_VERTICAL_ANCHOR_OPT = get_opt("y_axis_label_vertical_anchor", Y_AXIS_LABEL_VERTICAL_ANCHOR)
    Y_AXIS_SIDE_OPT = get_opt("y_axis_side", Y_AXIS_SIDE)
    Y_TICK_COUNT_OPT = get_opt("y_tick_count", Y_TICK_COUNT)
    Y_TICK_USE_COLORS_OPT = get_opt("y_tick_use_colors", Y_TICK_USE_COLORS)
    # Price labels
    USE_CENTS_OPT = get_opt("use_cents", USE_CENTS)
    CURRENCY_OVERRIDE_OPT = get_opt("currency_override", CURRENCY_OVERRIDE)
    LABEL_CURRENT_OPT = get_opt("label_current", LABEL_CURRENT)
    LABEL_CURRENT_AT_TOP_OPT = get_opt("label_current_at_top", LABEL_CURRENT_AT_TOP)
    LABEL_CURRENT_AT_TOP_FONT_WEIGHT_OPT = get_opt("label_current_at_top_font_weight", LABEL_CURRENT_AT_TOP_FONT_WEIGHT)
    LABEL_CURRENT_AT_TOP_PADDING_OPT = get_opt("label_current_at_top_padding", LABEL_CURRENT_AT_TOP_PADDING)
    LABEL_FONT_SIZE_OPT = get_opt("label_font_size", LABEL_FONT_SIZE)
    LABEL_FONT_WEIGHT_OPT = get_opt("label_font_weight", LABEL_FONT_WEIGHT)
    LABEL_MAX_OPT = get_opt("label_max", LABEL_MAX)
    LABEL_MAX_BELOW_POINT_OPT = get_opt("label_max_below_point", LABEL_MAX_BELOW_POINT)
    LABEL_MIN_OPT = get_opt("label_min", LABEL_MIN)
    LABEL_MINMAX_SHOW_PRICE_OPT = get_opt("label_minmax_show_price", LABEL_MINMAX_SHOW_PRICE)
    LABEL_SHOW_CURRENCY_OPT = get_opt("label_show_currency", LABEL_SHOW_CURRENCY)
    LABEL_USE_COLORS_OPT = get_opt("label_use_colors", LABEL_USE_COLORS)
    PRICE_DECIMALS_OPT = get_opt("price_decimals", PRICE_DECIMALS)
    COLOR_PRICE_LINE_BY_AVERAGE_OPT = get_opt("color_price_line_by_average", COLOR_PRICE_LINE_BY_AVERAGE)

    # Auto-determine price_decimals if not explicitly set (None = auto)
    if PRICE_DECIMALS_OPT is None:
        PRICE_DECIMALS_OPT = 0 if USE_CENTS_OPT else 2

    # Get transparent background option
    TRANSPARENT_BACKGROUND_OPT = get_opt("transparent_background", TRANSPARENT_BACKGROUND)

    # Select theme-specific constants based on THEME setting
    theme_prefix = "DARK_" if THEME_OPT == "dark" else "LIGHT_"

    # Load all theme constants with the selected prefix
    CHEAP_PRICE_COLOR = globals()[f"{theme_prefix}CHEAP_PRICE_COLOR"]
    FILL_ALPHA = globals()[f"{theme_prefix}FILL_ALPHA"]
    FILL_COLOR = globals()[f"{theme_prefix}FILL_COLOR"]
    GRID_ALPHA = globals()[f"{theme_prefix}GRID_ALPHA"]
    GRID_COLOR = globals()[f"{theme_prefix}GRID_COLOR"]
    LABEL_COLOR = globals()[f"{theme_prefix}LABEL_COLOR"]
    NOWLINE_ALPHA = globals()[f"{theme_prefix}NOWLINE_ALPHA"]
    NOWLINE_COLOR = globals()[f"{theme_prefix}NOWLINE_COLOR"]
    PLOT_LINEWIDTH = globals()[f"{theme_prefix}PLOT_LINEWIDTH"]
    PRICE_LINE_COLOR = globals()[f"{theme_prefix}PRICE_LINE_COLOR"]
    SPINE_COLOR = globals()[f"{theme_prefix}SPINE_COLOR"]
    STYLE_NAME = globals()[f"{theme_prefix}STYLE_NAME"]
    TICK_COLOR = globals()[f"{theme_prefix}TICK_COLOR"]
    TICKLINE_COLOR = globals()[f"{theme_prefix}TICKLINE_COLOR"]
    AXIS_LABEL_COLOR = globals()[f"{theme_prefix}AXIS_LABEL_COLOR"]
    LABEL_STROKE = globals()[f"{theme_prefix}LABEL_STROKE"]
    LABEL_COLOR_MIN = globals()[f"{theme_prefix}LABEL_COLOR_MIN"]
    LABEL_COLOR_MAX = globals()[f"{theme_prefix}LABEL_COLOR_MAX"]
    LABEL_COLOR_AVG = globals()[f"{theme_prefix}LABEL_COLOR_AVG"]
    PRICE_LINE_COLOR_ABOVE_AVG = globals()[f"{theme_prefix}PRICE_LINE_COLOR_ABOVE_AVG"]
    PRICE_LINE_COLOR_BELOW_AVG = globals()[f"{theme_prefix}PRICE_LINE_COLOR_BELOW_AVG"]
    PRICE_LINE_COLOR_NEAR_AVG = globals()[f"{theme_prefix}PRICE_LINE_COLOR_NEAR_AVG"]

    # Handle transparent background
    if TRANSPARENT_BACKGROUND_OPT:
        BACKGROUND_COLOR = "none"
    else:
        BACKGROUND_COLOR = globals()[f"{theme_prefix}BACKGROUND_COLOR"]

    fig_w = (CANVAS_WIDTH_OPT if FORCE_FIXED_SIZE_OPT else width) / 200
    fig_h = (CANVAS_HEIGHT_OPT if FORCE_FIXED_SIZE_OPT else height) / 200

    plt.close("all")
    plt.style.use(STYLE_NAME)
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=200)
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax = fig.add_subplot(111)
    ax.set_facecolor(BACKGROUND_COLOR)

    # Style spines and tick colors and place Y axis on configured side
    for name, spine in ax.spines.items():
        spine.set_edgecolor(SPINE_COLOR)
        # Control visibility of left/right spines based on configured side
        if name in ("left", "right"):
            if not SHOW_Y_AXIS_OPT:
                spine.set_visible(False)
            else:
                # Show only the configured side and hide the opposite
                if name == Y_AXIS_SIDE_OPT:
                    spine.set_visible(True)
                else:
                    spine.set_visible(False)

    # Configure Y ticks on chosen side
    if SHOW_Y_AXIS_OPT:
        if Y_AXIS_SIDE_OPT == "left":
            ax.yaxis.tick_left()
        else:
            ax.yaxis.tick_right()
    # Use ax.tick_params for this axes only and ensure only the chosen side shows labels
    # Y-axis label rotation: use the configured rotation angle
    # If rotation is 0, labels are horizontal
    # If rotation is non-zero, labels are rotated (typically 90 for left side, 270 for right side)
    y_rotation = Y_AXIS_LABEL_ROTATION_DEG_OPT

    # Calculate padding dynamically based on font size
    # Formula: padding = (font_size * 2 + 5) / 3
    # This gives: size 11→pad 9, size 13→pad 10, size 17→pad 13, size 20→pad 15
    # Use dynamic padding only when labels are rotated (non-zero rotation) and anchor mode is enabled
    y_padding = int((LABEL_FONT_SIZE_OPT * 2 + 5) / 3) if (Y_AXIS_LABEL_ROTATION_DEG_OPT != 0 and Y_AXIS_LABEL_VERTICAL_ANCHOR_OPT) else 3

    ax.tick_params(
        axis="y",
        colors=TICK_COLOR,
        labelleft=SHOW_Y_AXIS_OPT and Y_AXIS_SIDE_OPT == "left",
        labelright=SHOW_Y_AXIS_OPT and Y_AXIS_SIDE_OPT == "right",
        left=SHOW_Y_AXIS_TICKS_OPT and Y_AXIS_SIDE_OPT == "left",
        right=SHOW_Y_AXIS_TICKS_OPT and Y_AXIS_SIDE_OPT == "right",
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
    plt.tick_params(axis="both", which="both", bottom=False, labelbottom=False)

    # Price line and fill will be drawn after determining time range and "now" visibility
    # Cheap price point highlights will be drawn after determining visible data (at z-order 0.5, between background and fill)

    # Define X-range: show from start point to end point based on configuration
    if START_GRAPH_AT_OPT == START_GRAPH_AT_MIDNIGHT:
        # Start at local midnight
        start_hour = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        start_hour = start_hour if start_hour.tzinfo else start_hour.replace(tzinfo=LOCAL_TZ)

        # Apply hours limit if configured
        if HOURS_TO_SHOW_OPT is not None and HOURS_TO_SHOW_OPT > 0:
            # Show from midnight up to the configured number of hours OR last data point, whichever comes first
            hours_end = start_hour + datetime.timedelta(hours=HOURS_TO_SHOW_OPT)
            last_data_point = dates_plot[-1] if dates_plot else hours_end
            last_data_point = last_data_point if last_data_point.tzinfo else last_data_point.replace(tzinfo=LOCAL_TZ)
            end_hour = min(hours_end, last_data_point)
        else:
            # Default: show all available data from midnight to last data point
            end_hour = dates_plot[-1] if dates_plot else (start_hour + datetime.timedelta(days=1))
            end_hour = end_hour if end_hour.tzinfo else end_hour.replace(tzinfo=LOCAL_TZ)
    elif START_GRAPH_AT_OPT == START_GRAPH_AT_CURRENT_HOUR:
        # Start one hour before the current hour and show data up to the last available point
        start_hour = now_local.replace(minute=0, second=0, microsecond=0) - datetime.timedelta(hours=1)
        start_hour = start_hour if start_hour.tzinfo else start_hour.replace(tzinfo=LOCAL_TZ)

        # Apply hours limit if configured
        if HOURS_TO_SHOW_OPT is not None and HOURS_TO_SHOW_OPT > 0:
            # Show from one hour before current up to the configured number of hours OR last data point, whichever comes first
            hours_end = start_hour + datetime.timedelta(hours=HOURS_TO_SHOW_OPT)
            last_data_point = dates_plot[-1] if dates_plot else (start_hour + datetime.timedelta(hours=2))
            last_data_point = last_data_point if last_data_point.tzinfo else last_data_point.replace(tzinfo=LOCAL_TZ)
            end_hour = min(hours_end, last_data_point)
        else:
            # Default: end at the last available plotted data point instead of a fixed span
            end_hour = dates_plot[-1] if dates_plot else (start_hour + datetime.timedelta(hours=2))
            end_hour = end_hour if end_hour.tzinfo else end_hour.replace(tzinfo=LOCAL_TZ)

        # If the last data point is before the start_hour, ensure a minimal span
        if end_hour <= start_hour:
            end_hour = start_hour + datetime.timedelta(hours=2)
    else:  # START_GRAPH_AT_SHOW_ALL
        # Show all available data from first to last data point
        if dates_plot:
            start_hour = dates_plot[0]
            start_hour = start_hour if start_hour.tzinfo else start_hour.replace(tzinfo=LOCAL_TZ)
            end_hour = dates_plot[-1]
            end_hour = end_hour if end_hour.tzinfo else end_hour.replace(tzinfo=LOCAL_TZ)
        else:
            # Fallback if no data
            start_hour = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
            start_hour = start_hour if start_hour.tzinfo else start_hour.replace(tzinfo=LOCAL_TZ)
            end_hour = start_hour + datetime.timedelta(days=1)

        # Apply hours limit if configured (even in show_all mode)
        if HOURS_TO_SHOW_OPT is not None and HOURS_TO_SHOW_OPT > 0:
            hours_end = start_hour + datetime.timedelta(hours=HOURS_TO_SHOW_OPT)
            end_hour = min(hours_end, end_hour)

    # Check if "now" marker is visible within the time range
    now_is_visible = start_hour <= now_local <= end_hour

    # Identify and draw cheap price point highlights if configured
    # This is done before drawing the price line and fill so highlights appear behind the graph
    if CHEAP_PRICE_POINTS_OPT > 0 and dates_raw and prices_raw:
        # Determine step size for each period (quarter or hour)
        if len(dates_raw) >= 2:
            step_minutes = int((dates_raw[1] - dates_raw[0]).total_seconds() // 60) or 15
        else:
            step_minutes = 15
        period_duration = datetime.timedelta(minutes=step_minutes)

        # Group all price data by day (not just visible data)
        # This ensures we identify the cheapest periods per day across all available data
        from collections import defaultdict
        prices_by_day = defaultdict(list)

        for i, d in enumerate(dates_raw):
            day_key = d.date()  # Group by date (ignoring time)
            prices_by_day[day_key].append(i)

        # For each day, find the N cheapest periods
        cheap_indices_all_days = []
        for day_key, day_indices in prices_by_day.items():
            # Sort indices by price (ascending) for this day
            sorted_day_indices = sorted(day_indices, key=lambda i: prices_raw[i])
            # Take the N cheapest periods for this day
            cheap_for_day = sorted_day_indices[:min(CHEAP_PRICE_POINTS_OPT, len(sorted_day_indices))]
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

    # Draw price line, fill, and "now" line based on visibility
    # If COLOR_PRICE_LINE_BY_AVERAGE is enabled, color future segments with gradient transitions
    if COLOR_PRICE_LINE_BY_AVERAGE_OPT and prices_raw:
        # Calculate average price from all available data
        average_price = sum(prices_raw) / len(prices_raw)

        # Import necessary for gradient coloring
        import numpy as np

        if now_is_visible:
            # Split the data into past (dimmed) and future (bright) sections
            past_dates = []
            past_prices = []
            future_dates = []
            future_prices = []

            for i, (d, p) in enumerate(zip(dates_plot, prices_plot)):
                if d <= now_local:
                    past_dates.append(d)
                    past_prices.append(p)
                if d >= now_local:
                    future_dates.append(d)
                    future_prices.append(p)

            # Ensure continuity at the "now" point
            if past_dates and future_dates:
                if past_dates[-1] != now_local and future_dates[0] != now_local:
                    if past_prices:
                        past_dates.append(now_local)
                        past_prices.append(past_prices[-1])
                    if future_prices:
                        future_dates.insert(0, now_local)
                        future_prices.insert(0, future_prices[0])

            # Draw dimmed fill and line for past data (use default color, no coloring)
            if past_dates and past_prices:
                ax.fill_between(past_dates, 0, past_prices, facecolor=FILL_COLOR, alpha=FILL_ALPHA * 0.3, step="post", zorder=1)
                # Use default price line color for past data
                ax.step(past_dates, past_prices, PRICE_LINE_COLOR, where="post", linewidth=PLOT_LINEWIDTH, alpha=0.3, zorder=4)

            # Draw bright fill for future data
            if future_dates and future_prices:
                ax.fill_between(future_dates, 0, future_prices, facecolor=FILL_COLOR, alpha=FILL_ALPHA, step="post", zorder=1)

                # Draw colored segments for future data with gradient effect
                if len(future_dates) > 1:
                    for i in range(len(future_dates) - 1):
                        color = _get_price_color(future_prices[i], average_price, NEAR_AVERAGE_THRESHOLD,
                                                PRICE_LINE_COLOR_BELOW_AVG, PRICE_LINE_COLOR_NEAR_AVG,
                                                PRICE_LINE_COLOR_ABOVE_AVG)
                        # Draw horizontal segment
                        ax.plot([future_dates[i], future_dates[i + 1]], [future_prices[i], future_prices[i]],
                               color=color, linewidth=PLOT_LINEWIDTH, zorder=4)
                        # Draw vertical segment with interpolated color
                        if i + 1 < len(future_prices) - 1:
                            # Interpolate color for vertical segment between current and next price
                            color_next = _get_price_color(future_prices[i + 1], average_price, NEAR_AVERAGE_THRESHOLD,
                                                          PRICE_LINE_COLOR_BELOW_AVG, PRICE_LINE_COLOR_NEAR_AVG,
                                                          PRICE_LINE_COLOR_ABOVE_AVG)
                            # Create gradient on vertical segment
                            n_points = 10
                            y_vals = np.linspace(future_prices[i], future_prices[i + 1], n_points)
                            for j in range(n_points - 1):
                                ratio = j / (n_points - 1)
                                interp_color = tuple(color[k] + (color_next[k] - color[k]) * ratio for k in range(3))
                                ax.plot([future_dates[i + 1], future_dates[i + 1]],
                                       [y_vals[j], y_vals[j + 1]],
                                       color=interp_color, linewidth=PLOT_LINEWIDTH, zorder=4)
                        else:
                            # Last vertical segment
                            ax.plot([future_dates[i + 1], future_dates[i + 1]],
                                   [future_prices[i], future_prices[i + 1]],
                                   color=color, linewidth=PLOT_LINEWIDTH, zorder=4)
        else:
            # "Now" marker is not visible - draw fully bright colored line and fill
            ax.fill_between(dates_plot, 0, prices_plot, facecolor=FILL_COLOR, alpha=FILL_ALPHA, step="post", zorder=1)

            # Draw colored segments with gradient effect
            if len(dates_plot) > 1:
                for i in range(len(dates_plot) - 1):
                    color = _get_price_color(prices_plot[i], average_price, NEAR_AVERAGE_THRESHOLD,
                                            PRICE_LINE_COLOR_BELOW_AVG, PRICE_LINE_COLOR_NEAR_AVG,
                                            PRICE_LINE_COLOR_ABOVE_AVG)
                    # Draw horizontal segment
                    ax.plot([dates_plot[i], dates_plot[i + 1]], [prices_plot[i], prices_plot[i]],
                           color=color, linewidth=PLOT_LINEWIDTH, zorder=4)
                    # Draw vertical segment with interpolated color
                    if i + 1 < len(prices_plot) - 1:
                        color_next = _get_price_color(prices_plot[i + 1], average_price, NEAR_AVERAGE_THRESHOLD,
                                                      PRICE_LINE_COLOR_BELOW_AVG, PRICE_LINE_COLOR_NEAR_AVG,
                                                      PRICE_LINE_COLOR_ABOVE_AVG)
                        # Create gradient on vertical segment
                        n_points = 10
                        y_vals = np.linspace(prices_plot[i], prices_plot[i + 1], n_points)
                        for j in range(n_points - 1):
                            ratio = j / (n_points - 1)
                            interp_color = tuple(color[k] + (color_next[k] - color[k]) * ratio for k in range(3))
                            ax.plot([dates_plot[i + 1], dates_plot[i + 1]],
                                   [y_vals[j], y_vals[j + 1]],
                                   color=interp_color, linewidth=PLOT_LINEWIDTH, zorder=4)
                    else:
                        # Last vertical segment
                        ax.plot([dates_plot[i + 1], dates_plot[i + 1]],
                               [prices_plot[i], prices_plot[i + 1]],
                               color=color, linewidth=PLOT_LINEWIDTH, zorder=4)

        # Draw "now" line on top (always drawn)
        ax.axvline(now_local, color=NOWLINE_COLOR, alpha=NOWLINE_ALPHA, linestyle="-", zorder=5)
    else:
        # Original single-color rendering (when COLOR_PRICE_LINE_BY_AVERAGE is disabled)
        if now_is_visible:
            # Split the data into past (dimmed) and future (bright) sections
            past_dates = []
            past_prices = []
            future_dates = []
            future_prices = []

            for i, (d, p) in enumerate(zip(dates_plot, prices_plot)):
                if d <= now_local:
                    past_dates.append(d)
                    past_prices.append(p)
                if d >= now_local:
                    future_dates.append(d)
                    future_prices.append(p)

            # Ensure continuity at the "now" point
            if past_dates and future_dates:
                if past_dates[-1] != now_local and future_dates[0] != now_local:
                    if past_prices:
                        past_dates.append(now_local)
                        past_prices.append(past_prices[-1])
                    if future_prices:
                        future_dates.insert(0, now_local)
                        future_prices.insert(0, future_prices[0])

            # Draw dimmed line and fill for past data
            if past_dates and past_prices:
                ax.fill_between(past_dates, 0, past_prices, facecolor=FILL_COLOR, alpha=FILL_ALPHA * 0.3, step="post", zorder=1)
                ax.step(past_dates, past_prices, PRICE_LINE_COLOR, where="post", linewidth=PLOT_LINEWIDTH, alpha=0.3, zorder=4)

            # Draw bright line and fill for future data
            if future_dates and future_prices:
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
    # This applies regardless of where the current price label is shown
    # The glow effect is always rendered to highlight the current price on the graph
    if LABEL_CURRENT_OPT and now_is_visible and idx < len(prices_raw):
        current_price = prices_raw[idx]
        # Draw multiple overlapping circles with decreasing alpha for glow effect
        for size_factor, alpha_factor in [(3.0, 0.15), (2.0, 0.3), (1.0, 0.8)]:
            ax.plot(now_local, current_price, 'o',
                   color=NOWLINE_COLOR,
                   markersize=8 * size_factor,
                   alpha=NOWLINE_ALPHA * alpha_factor,
                   zorder=5)

    # Compute visible prices from the plotted points (dates_plot/prices_plot)
    # Use numeric timestamps instead of relying on hour values so ranges that
    # cross midnight (and thus wrap hour numbers) are handled correctly.
    start_ts = start_hour.timestamp()
    end_ts = end_hour.timestamp()

    # Filter visible data in one pass - build both prices and indices lists simultaneously
    visible_prices = []
    visible_indices = []
    for i, (d, p) in enumerate(zip(dates_plot, prices_plot)):
        if start_ts <= d.timestamp() <= end_ts:
            visible_prices.append(p)
            # Only track indices that correspond to raw data (plot has one extra point)
            if i < len(dates_raw):
                visible_indices.append(i)

    # Fallback if no visible data found
    if not visible_prices:
        visible_prices = prices_plot or prices_raw or [0]
    if not visible_indices and prices_raw:
        visible_indices = list(range(len(prices_raw)))

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
        if LABEL_CURRENT_OPT and current_idx is not None:
            chosen.add(current_idx)
            # Don't label min/max if they coincide with current
            if LABEL_MIN_OPT and min_idx is not None and min_idx != current_idx:
                chosen.add(min_idx)
            if LABEL_MAX_OPT and max_idx is not None and max_idx != current_idx:
                chosen.add(max_idx)
        else:
            if LABEL_MIN_OPT and min_idx is not None:
                chosen.add(min_idx)
            if LABEL_MAX_OPT and max_idx is not None:
                chosen.add(max_idx)

    # Pre-calculate label settings once to avoid repeated calculations
    label_effects = [pe.withStroke(linewidth=2, foreground=BACKGROUND_COLOR)] if LABEL_STROKE else None
    price_multiplier = 100 if USE_CENTS_OPT else 1
    decimals = PRICE_DECIMALS_OPT
    currency_label = f" {currency}" if (LABEL_SHOW_CURRENCY_OPT and currency) else ""

    # Draw labels for chosen data points (min, max, current)
    for i in sorted(chosen):
        # Skip current label here if it will be drawn at top of chart
        if LABEL_CURRENT_OPT and i == current_idx and LABEL_CURRENT_AT_TOP_OPT:
            continue

        # Classify this point to determine styling
        is_min = (min_idx is not None and i == min_idx)
        is_max = (max_idx is not None and i == max_idx)
        is_current = (current_idx is not None and i == current_idx)

        # Determine if price should be shown (can be disabled for min/max)
        show_price = not ((is_min or is_max) and not LABEL_MINMAX_SHOW_PRICE_OPT)

        # Build label text: price + time or just time
        # For current price, show minutes; for min/max, show only hour
        time_str = now_local.strftime('%H:%M') if is_current else dates_raw[i].strftime('%H')
        if show_price:
            price_display = prices_raw[i] * price_multiplier
            label_text = f"{price_display:.{decimals}f}{currency_label}\nat {time_str}"
        else:
            label_text = time_str

        # Set vertical alignment:
        # - Current labels always use "bottom" (above point) for in-graph labels
        # - Max labels use "top" (below point) if LABEL_MAX_BELOW_POINT or LABEL_CURRENT_AT_TOP is enabled
        # - Min labels always use "bottom" (above point)
        if is_current:
            vertical_align = "bottom"
        elif is_max and (LABEL_MAX_BELOW_POINT_OPT or LABEL_CURRENT_AT_TOP_OPT):
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
            if COLOR_PRICE_LINE_BY_AVERAGE_OPT and prices_raw and not is_past:
                # Calculate average price from all available data
                average_price = sum(prices_raw) / len(prices_raw)
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
    if LABEL_CURRENT_OPT and current_idx is not None and LABEL_CURRENT_AT_TOP_OPT:
        price_display = prices_raw[current_idx] * price_multiplier
        now_time = now_local.strftime("%H:%M")
        ax_pos = ax.get_position()
        # Center the label horizontally within the graph area
        label_x = (ax_pos.x0 + ax_pos.x1) / 2
        # Padding now counts from bottom of text (va="bottom")
        label_y = 1.0 - LABEL_CURRENT_AT_TOP_PADDING_OPT

        fig.text(
            label_x,
            label_y,
            f"{price_display:.{decimals}f}{currency_label} at {now_time}",
            fontsize=LABEL_FONT_SIZE_OPT,
            color=LABEL_COLOR,
            fontweight=LABEL_CURRENT_AT_TOP_FONT_WEIGHT_OPT,
            va="bottom",
            ha="center",
            zorder=7,
            path_effects=label_effects,
        )

    # Set X-axis range and Y-axis limits based on visible data
    ax.set_xlim((start_hour, end_hour))
    # Add padding proportional to the price range to prevent data from touching the edges
    # Use 5% padding at both bottom and top
    pad_low = max(price_range * 0.05, 0.01)  # At least 0.01 to handle very small ranges
    pad_high = max(price_range * 0.05, 0.01)  # At least 0.01 to handle very small ranges
    ax.set_ylim((y_min - pad_low, y_max + pad_high))

    # Draw average price line if enabled (at same z-order as horizontal grid lines)
    # Average is calculated from all available price data (past and future), not just the visible period
    if SHOW_AVERAGE_PRICE_LINE_OPT and prices_raw:
        average_price = sum(prices_raw) / len(prices_raw)
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
    if SHOW_Y_AXIS_OPT:
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
                    # Show average of all available prices (consistent with average price line)
                    y_avg = sum(prices_raw) / len(prices_raw)
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
                    # Show min, max, and average of all available prices (consistent with average price line)
                    y_avg = sum(prices_raw) / len(prices_raw)
                    ax.yaxis.set_major_locator(mticker.FixedLocator([y_min_tick, y_avg, y_max_tick]))
                    if Y_TICK_USE_COLORS_OPT:
                        tick_labels = ax.yaxis.get_ticklabels()
                        if len(tick_labels) >= 3:
                            tick_labels[0].set_color(LABEL_COLOR_MIN)
                            tick_labels[1].set_color(LABEL_COLOR_AVG)
                            tick_labels[2].set_color(LABEL_COLOR_MAX)

                elif Y_TICK_COUNT_OPT >= 4:
                    # Show evenly distributed ticks between min and max (excluding edges)
                    step = (y_max_tick - y_min_tick) / (Y_TICK_COUNT_OPT + 1)
                    tick_positions = [y_min_tick + step * (i + 1) for i in range(Y_TICK_COUNT_OPT)]
                    ax.yaxis.set_major_locator(mticker.FixedLocator(tick_positions))
            except Exception:
                # Silently ignore errors in tick configuration (e.g., division by zero)
                pass

    # Draw X-axis tick lines and labels manually
    # Generate tick times at configured intervals
    tick_times = []
    t = start_hour
    while t <= end_hour:
        tick_times.append(t)
        t += datetime.timedelta(hours=X_TICK_STEP_HOURS_OPT)

    ylim = ax.get_ylim()
    xlab_effects = [pe.withStroke(linewidth=2, foreground=BACKGROUND_COLOR)] if LABEL_STROKE else None

    # Enable X-ticks at the tick positions if configured
    if SHOW_X_TICKS_OPT:
        ax.set_xticks(tick_times)
        ax.tick_params(axis="x", which="both", bottom=True, top=False, labelbottom=False, color=TICK_COLOR)

    # Draw time labels (and optionally vertical grid lines if show_vertical_grid is enabled)
    for tt in tick_times:
        # Draw vertical grid lines only if show_vertical_grid is enabled
        # These are independent of show_x_ticks setting
        # Use same linewidth and alpha as horizontal grid for consistency
        if SHOW_VERTICAL_GRID_OPT:
            ax.vlines([tt], ymin=ylim[0], ymax=ylim[1], colors=GRID_COLOR, linewidth=1.0, alpha=GRID_ALPHA, zorder=2)
        ax.text(
            tt,
            -X_AXIS_LABEL_Y_OFFSET,
            tt.strftime("%H"),
            transform=ax.get_xaxis_transform(),
            rotation=0,
            ha="center",
            va="top",
            fontsize=LABEL_FONT_SIZE_OPT,
            color=AXIS_LABEL_COLOR,
            clip_on=False,
            zorder=6,
            path_effects=xlab_effects,
        )

    # Finalize plot layout and save
    ax.margins(x=0)
    fig.subplots_adjust(bottom=BOTTOM_MARGIN_OPT, left=LEFT_MARGIN_OPT, right=1-LEFT_MARGIN_OPT)

    try:
        # Save with correct figure background to avoid white edges
        fig.savefig(out_path, facecolor=fig.get_facecolor())
    finally:
        # Clean up to prevent memory leaks
        plt.close(fig)
        plt.close("all")
