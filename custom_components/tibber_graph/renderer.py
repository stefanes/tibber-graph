"""Rendering logic for Tibber price graphs using matplotlib."""
import datetime

from dateutil import tz
import matplotlib
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Import all default configuration values from defaults.py
from .defaults import *

# Matplotlib heavy imports: import once at module load to reduce per-render overhead
matplotlib.use("Agg")

# Apply global rc settings once
plt.rcdefaults()
plt.rcParams.update({'font.size': 12})

# Reuse local timezone object
LOCAL_TZ = tz.tzlocal()


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
    START_AT_MIDNIGHT_OPT = get_opt("start_at_midnight", START_AT_MIDNIGHT)
    X_AXIS_LABEL_ROTATION_DEG_OPT = get_opt("x_axis_label_rotation_deg", X_AXIS_LABEL_ROTATION_DEG)
    X_TICK_STEP_HOURS_OPT = get_opt("x_tick_step_hours", X_TICK_STEP_HOURS)
    # Y-axis settings
    SHOW_Y_AXIS_OPT = get_opt("show_y_axis", SHOW_Y_AXIS)
    SHOW_Y_GRID_OPT = get_opt("show_y_grid", SHOW_Y_GRID)
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

    # Auto-determine price_decimals if not explicitly set (None = auto)
    if PRICE_DECIMALS_OPT is None:
        PRICE_DECIMALS_OPT = 0 if USE_CENTS_OPT else 2

    # Select theme-specific constants based on THEME setting
    theme_prefix = "DARK_" if THEME_OPT == "dark" else "LIGHT_"
    BACKGROUND_COLOR = globals()[f"{theme_prefix}BACKGROUND_COLOR"]
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

    # Optional Y-grid
    if SHOW_Y_GRID_OPT:
        ax.grid(which="major", axis="y", linestyle="-", color=GRID_COLOR, alpha=GRID_ALPHA)
    else:
        ax.grid(False)
    # Disable auto X-ticks (we'll draw them manually). Don't set left labels here to avoid
    # interfering with Y_AXIS_SIDE; that is handled per-axis above.
    plt.tick_params(axis="both", which="both", bottom=False, labelbottom=False)

    # Vertical "now" line
    ax.axvline(now_local, color=NOWLINE_COLOR, alpha=NOWLINE_ALPHA, linestyle="-", zorder=2)

    # Price line and fill
    ax.step(dates_plot, prices_plot, PRICE_LINE_COLOR, where="post", linewidth=PLOT_LINEWIDTH)
    ax.fill_between(dates_plot, 0, prices_plot, facecolor=FILL_COLOR, alpha=FILL_ALPHA, step="post")

    # Define X-range: can either show from midnight-to-midnight or from one hour before current to last data point
    if START_AT_MIDNIGHT_OPT:
        # Start at local midnight and show 24 hours
        start_hour = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        start_hour = start_hour if start_hour.tzinfo else start_hour.replace(tzinfo=LOCAL_TZ)
        end_hour = start_hour + datetime.timedelta(days=1)
    else:
        # Start one hour before the current hour and show data up to the last available point
        start_hour = now_local.replace(minute=0, second=0, microsecond=0) - datetime.timedelta(hours=1)
        start_hour = start_hour if start_hour.tzinfo else start_hour.replace(tzinfo=LOCAL_TZ)
        # End at the last available plotted data point instead of a fixed 24h span
        end_hour = dates_plot[-1] if dates_plot else (start_hour + datetime.timedelta(hours=2))
        end_hour = end_hour if end_hour.tzinfo else end_hour.replace(tzinfo=LOCAL_TZ)
        # If the last data point is before the start_hour, ensure a minimal span
        if end_hour <= start_hour:
            end_hour = start_hour + datetime.timedelta(hours=2)

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

    # Determine which data points to label (min, max, current) based on visible data
    chosen = set()
    min_idx = None
    max_idx = None
    current_idx = None

    if prices_raw:
        # Determine which indices to consider for min/max labels
        # If START_AT_MIDNIGHT: consider entire visible range (past and future)
        # Otherwise: only consider future prices (from current time onwards)
        if START_AT_MIDNIGHT_OPT:
            candidate_indices = visible_indices
        else:
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
    label_effects = [pe.withStroke(linewidth=2, foreground="#00000080")] if LABEL_STROKE else None
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
        time_str = now_local.strftime('%H:%M') if is_current else dates_raw[i].strftime('%H:%M')
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

        ax.text(
            dates_raw[i],
            prices_raw[i],
            label_text,
            fontsize=LABEL_FONT_SIZE_OPT,
            va=vertical_align,
            ha="center",
            color=label_color,
            fontweight=LABEL_FONT_WEIGHT_OPT,
            zorder=3,
            path_effects=label_effects,
        )

    # Draw current price label at fixed position (top left above graph) if enabled
    if LABEL_CURRENT_OPT and current_idx is not None and LABEL_CURRENT_AT_TOP_OPT:
        price_display = prices_raw[current_idx] * price_multiplier
        now_time = now_local.strftime("%H:%M")
        ax_pos = ax.get_position()
        label_y = 1.0 - LABEL_CURRENT_AT_TOP_PADDING_OPT

        fig.text(
            ax_pos.x0,
            label_y,
            f"{price_display:.{decimals}f}{currency_label} at {now_time}",
            fontsize=LABEL_FONT_SIZE_OPT,
            color=LABEL_COLOR,
            fontweight=LABEL_CURRENT_AT_TOP_FONT_WEIGHT_OPT,
            va="top",
            ha="left",
            zorder=20,
            path_effects=label_effects,
        )

    # Set X-axis range and Y-axis limits based on visible data
    ax.set_xlim((start_hour, end_hour))
    y_min = min(visible_prices)
    y_max = max(visible_prices)
    # Add small padding to prevent data from touching the edges
    pad_low = 0.005
    pad_high = 0.0075
    ax.set_ylim((y_min - pad_low, y_max + pad_high))

    # Calculate Y-axis tick min/max values
    # Key difference: For labels we use strict future (>), but for ticks we use current hour onwards (>=)
    # When not starting at midnight, ticks should only consider future prices (from current hour onwards)
    if START_AT_MIDNIGHT_OPT:
        # Use all visible prices for ticks (past and future)
        y_min_tick = y_min
        y_max_tick = y_max
        prices_for_ticks = visible_prices
    elif candidate_indices:
        # Use only future prices for ticks (from current hour onwards for hourly data)
        # This ensures ticks reflect only what's ahead, not what's already past
        now_hour_start = now_local.replace(minute=0, second=0, microsecond=0)
        future_indices = [i for i in visible_indices if dates_raw[i] >= now_hour_start]

        if future_indices:
            future_prices = [prices_raw[i] for i in future_indices]
            y_min_tick = min(future_prices)
            y_max_tick = max(future_prices)
            prices_for_ticks = future_prices
        else:
            # Fallback to all visible prices if no future prices
            y_min_tick = y_min
            y_max_tick = y_max
            prices_for_ticks = visible_prices
    else:
        # Fallback to all visible prices if no candidates
        y_min_tick = y_min
        y_max_tick = y_max
        prices_for_ticks = visible_prices

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
                    # Show average of prices (future only if not START_AT_MIDNIGHT)
                    y_avg = sum(prices_for_ticks) / len(prices_for_ticks)
                    ax.yaxis.set_major_locator(mticker.FixedLocator([y_avg]))
                    if Y_TICK_USE_COLORS_OPT:
                        for tick_label in ax.yaxis.get_ticklabels():
                            tick_label.set_color(LABEL_COLOR_AVG)

                elif Y_TICK_COUNT_OPT == 2:
                    # Show min and max (future only if not START_AT_MIDNIGHT)
                    ax.yaxis.set_major_locator(mticker.FixedLocator([y_min_tick, y_max_tick]))
                    if Y_TICK_USE_COLORS_OPT:
                        tick_labels = ax.yaxis.get_ticklabels()
                        if len(tick_labels) >= 2:
                            tick_labels[0].set_color(LABEL_COLOR_MIN)
                            tick_labels[1].set_color(LABEL_COLOR_MAX)

                elif Y_TICK_COUNT_OPT == 3:
                    # Show min, max, and average (future only if not START_AT_MIDNIGHT)
                    y_avg = sum(prices_for_ticks) / len(prices_for_ticks)
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
    xlab_effects = [pe.withStroke(linewidth=2, foreground="#00000080")] if LABEL_STROKE else None

    # Enable X-ticks at the tick positions if configured
    if SHOW_X_TICKS_OPT:
        ax.set_xticks(tick_times)
        ax.tick_params(axis="x", which="both", bottom=True, top=False, labelbottom=False, color=TICK_COLOR)

    # Draw vertical tick lines and time labels
    for tt in tick_times:
        ax.vlines([tt], ymin=ylim[0], ymax=ylim[1], colors=TICKLINE_COLOR, linewidth=1.5, alpha=1.0, zorder=1)
        ax.text(
            tt,
            -X_AXIS_LABEL_Y_OFFSET,
            tt.strftime("%H:%M"),
            transform=ax.get_xaxis_transform(),
            rotation=X_AXIS_LABEL_ROTATION_DEG_OPT,
            ha="right",
            va="top",
            fontsize=LABEL_FONT_SIZE_OPT,
            color=AXIS_LABEL_COLOR,
            clip_on=False,
            zorder=10,
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
