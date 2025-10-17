"""Rendering logic for Tibber price graphs using matplotlib."""
import datetime

from dateutil import tz
import matplotlib
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from .config import *

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
        currency: Currency code string (e.g., "EUR", "SEK", "NOK")
        out_path: Output file path for the rendered image
    """
    # Matplotlib imports and rc settings are prepared at module import to
    # minimize per-render overhead.
    # Use the module-level plt, mticker, pe that were imported earlier.

    # Select theme-specific constants based on THEME setting
    theme_prefix = "DARK_" if THEME == "dark" else "LIGHT_"
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

    fig_w = (CANVAS_WIDTH if FORCE_FIXED_SIZE else width) / 200
    fig_h = (CANVAS_HEIGHT if FORCE_FIXED_SIZE else height) / 200

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
            if not SHOW_Y_AXIS:
                spine.set_visible(False)
            else:
                # Show only the configured side and hide the opposite
                if name == Y_AXIS_SIDE:
                    spine.set_visible(True)
                else:
                    spine.set_visible(False)

    # Configure Y ticks on chosen side
    if SHOW_Y_AXIS:
        if Y_AXIS_SIDE == "left":
            ax.yaxis.tick_left()
        else:
            ax.yaxis.tick_right()
    # Use ax.tick_params for this axes only and ensure only the chosen side shows labels
    # Calculate Y-axis label rotation based on side:
    # - Left side: 90° (label reads bottom-to-top, starts at tick)
    # - Right side: 270° (label reads top-to-bottom, ends at tick)
    if Y_AXIS_LABEL_VERTICAL:
        y_rotation = 90 if Y_AXIS_SIDE == "left" else 270
    else:
        y_rotation = 0

    ax.tick_params(
        axis="y",
        colors=TICK_COLOR,
        labelleft=SHOW_Y_AXIS and Y_AXIS_SIDE == "left",
        labelright=SHOW_Y_AXIS and Y_AXIS_SIDE == "right",
        labelsize=(Y_AXIS_LABEL_FONT_SIZE),
        rotation=y_rotation,
        pad=Y_AXIS_LABEL_PADDING,
    )

    # Set rotation_mode for vertical labels based on anchor setting
    if Y_AXIS_LABEL_VERTICAL:
        for label in ax.yaxis.get_ticklabels():
            # 'anchor' mode aligns label edge with tick, 'default' centers label on tick
            label.set_rotation_mode('anchor' if Y_AXIS_LABEL_VERTICAL_ANCHOR else 'default')

    # Optional Y-grid
    if SHOW_Y_GRID:
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
    if START_AT_MIDNIGHT:
        # Start at local midnight
        start_hour = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        start_hour = start_hour if start_hour.tzinfo else start_hour.replace(tzinfo=LOCAL_TZ)
        end_hour = start_hour + datetime.timedelta(days=1)
    else:
        # Start one hour before the current hour
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

    # Filter visible data in one pass
    visible_prices = []
    visible_indices = []
    for i, (d, p) in enumerate(zip(dates_plot, prices_plot)):
        d_ts = d.timestamp()
        if start_ts <= d_ts <= end_ts:
            visible_prices.append(p)
            if i < len(dates_raw):
                visible_indices.append(i)

    if not visible_prices:
        # Fallback to raw prices or the provided plot prices
        visible_prices = prices_plot or prices_raw or [0]

    if not visible_indices and prices_raw:
        # Fallback to all indices
        visible_indices = list(range(len(prices_raw)))

    # Now determine which labels to show (min, max, current) based on visible data only
    chosen = set()
    min_idx = None
    max_idx = None
    current_idx = None

    if prices_raw:
        # Determine which indices to consider for min/max
        # If START_AT_MIDNIGHT, consider entire visible range; otherwise only future prices
        if START_AT_MIDNIGHT:
            # Consider all visible indices for min/max
            candidate_indices = visible_indices
        else:
            # Only consider indices at or after now_local for min/max
            candidate_indices = [i for i in visible_indices if dates_raw[i] > now_local]

        min_idx = min(candidate_indices, key=lambda i: prices_raw[i]) if candidate_indices else None
        max_idx = max(candidate_indices, key=lambda i: prices_raw[i]) if candidate_indices else None
        current_idx = idx if idx in visible_indices else None
        # If labeling current, do not label min/max if it is at the same time as current
        if LABEL_CURRENT and current_idx is not None:
            chosen.add(current_idx)
            if LABEL_MIN and min_idx is not None and min_idx != current_idx:
                chosen.add(min_idx)
            if LABEL_MAX and max_idx is not None and max_idx != current_idx:
                chosen.add(max_idx)
        else:
            if LABEL_MIN and min_idx is not None:
                chosen.add(min_idx)
            if LABEL_MAX and max_idx is not None:
                chosen.add(max_idx)

    # Pre-calculate label settings once
    label_effects = [pe.withStroke(linewidth=2, foreground="#00000080")] if LABEL_STROKE else None
    price_multiplier = 100 if USE_CENTS else 1
    decimals = 0 if USE_CENTS else PRICE_DECIMALS
    # Show currency on price labels if configured
    currency_label = f" {currency}" if (LABEL_SHOW_CURRENCY and currency) else ""

    for i in sorted(chosen):
        # Only label min/max here; current will be handled separately if LABEL_CURRENT_AT_TOP
        if LABEL_CURRENT and i == current_idx and LABEL_CURRENT_AT_TOP:
            continue

        # Determine if this is min or max to check if we should show price
        is_min = (min_idx is not None and i == min_idx)
        is_max = (max_idx is not None and i == max_idx)
        is_current = (current_idx is not None and i == current_idx)
        show_price = True

        if (is_min or is_max) and not LABEL_MINMAX_SHOW_PRICE:
            show_price = False

        # Build label text
        if show_price:
            price_display = prices_raw[i] * price_multiplier
            label_text = f"{price_display:.{decimals}f}{currency_label}\nat {dates_raw[i].strftime('%H:%M')}"
        else:
            label_text = dates_raw[i].strftime('%H:%M')

        # Set vertical alignment: max labels optionally go below (top alignment) if configured
        vertical_align = "top" if (is_max and LABEL_MAX_BELOW_POINT) else "bottom"

        # Determine label color: use colored labels if enabled, otherwise use default
        # Only color min/max labels when LABEL_USE_COLORS is enabled
        if LABEL_USE_COLORS:
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
            fontsize=LABEL_FONT_SIZE,
            va=vertical_align,
            ha="center",
            color=label_color,
            fontweight=LABEL_FONT_WEIGHT,
            zorder=3,
            path_effects=label_effects,
        )

    # Draw current label at fixed position (top left above graph) if enabled
    if LABEL_CURRENT and current_idx is not None and LABEL_CURRENT_AT_TOP:
        price_display = prices_raw[current_idx] * price_multiplier
        # Use the current local time for the label
        now_time = now_local.strftime("%H:%M")
        # Align label with the left edge of the graph canvas
        ax_pos = ax.get_position()
        # Always show currency for top label (for clarity and consistency)
        currency_label = f" {currency}" if currency else ""
        # Calculate vertical position with padding from top
        label_y = 1.0 - LABEL_CURRENT_AT_TOP_PADDING
        # Current label always uses default axis label color
        fig.text(
            ax_pos.x0,
            label_y,  # x, y in figure coordinates (top left with padding)
            f"{price_display:.{decimals}f}{currency_label} at {now_time}",
            fontsize=LABEL_CURRENT_AT_TOP_FONT_SIZE,
            color=LABEL_COLOR,
            fontweight=LABEL_CURRENT_AT_TOP_FONT_WEIGHT,
            va="top",
            ha="left",
            zorder=20,
            path_effects=label_effects,
        )

    # Apply X-range and Y-limits based on visible prices
    ax.set_xlim((start_hour, end_hour))
    y_min = min(visible_prices)
    y_max = max(visible_prices)
    # Add small padding
    pad_low = 0.005
    pad_high = 0.0075
    ax.set_ylim((y_min - pad_low, y_max + pad_high))

    # Format Y-axis (only when Y axis is visible)
    if SHOW_Y_AXIS:
        # When showing cents, multiply axis values by 100
        decimals_axis = 0 if USE_CENTS else PRICE_DECIMALS
        if USE_CENTS:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, pos: f"{v * 100:.{decimals_axis}f}"))
        else:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, pos: f"{v:.{decimals_axis}f}"))
        # Apply tick count if configured
        if Y_TICK_COUNT:
            try:
                if Y_TICK_COUNT == 1:
                    # Show average of visible prices as the single tick
                    y_avg = sum(visible_prices) / len(visible_prices)
                    ax.yaxis.set_major_locator(mticker.FixedLocator([y_avg]))
                    # Color the avg tick if Y-axis tick colors are enabled
                    if Y_TICK_USE_COLORS:
                        for tick_label in ax.yaxis.get_ticklabels():
                            tick_label.set_color(LABEL_COLOR_AVG)
                elif Y_TICK_COUNT == 2:
                    # Show min and max
                    ax.yaxis.set_major_locator(mticker.FixedLocator([y_min, y_max]))
                    # Color the min/max ticks if Y-axis tick colors are enabled
                    if Y_TICK_USE_COLORS:
                        tick_labels = ax.yaxis.get_ticklabels()
                        if len(tick_labels) >= 2:
                            tick_labels[0].set_color(LABEL_COLOR_MIN)
                            tick_labels[1].set_color(LABEL_COLOR_MAX)
                elif Y_TICK_COUNT == 3:
                    # Show min, max, and average
                    y_avg = sum(visible_prices) / len(visible_prices)
                    ax.yaxis.set_major_locator(mticker.FixedLocator([y_min, y_avg, y_max]))
                    # Color the min/avg/max ticks if Y-axis tick colors are enabled
                    if Y_TICK_USE_COLORS:
                        tick_labels = ax.yaxis.get_ticklabels()
                        if len(tick_labels) >= 3:
                            tick_labels[0].set_color(LABEL_COLOR_MIN)
                            tick_labels[1].set_color(LABEL_COLOR_AVG)
                            tick_labels[2].set_color(LABEL_COLOR_MAX)
                elif Y_TICK_COUNT >= 4:
                    # Show evenly distributed ticks, excluding min and max at the edges
                    # Distribute Y_TICK_COUNT ticks evenly within the range (not at min/max)
                    step = (y_max - y_min) / (Y_TICK_COUNT + 1)
                    tick_positions = [y_min + step * (i + 1) for i in range(Y_TICK_COUNT)]
                    ax.yaxis.set_major_locator(mticker.FixedLocator(tick_positions))
            except Exception:
                pass

    # Manually draw X-axis lines, labels, and set ticks
    tick_times = []
    t = start_hour
    while t <= end_hour:
        tick_times.append(t)
        t += datetime.timedelta(hours=X_TICK_STEP_HOURS)

    ylim = ax.get_ylim()
    xlab_effects = [pe.withStroke(linewidth=2, foreground="#00000080")] if LABEL_STROKE else None

    # Set x-ticks at the same positions if enabled
    if SHOW_X_TICKS:
        ax.set_xticks(tick_times)
        ax.tick_params(axis="x", which="both", bottom=True, top=False, labelbottom=False, color=TICK_COLOR)

    for tt in tick_times:
        ax.vlines([tt], ymin=ylim[0], ymax=ylim[1], colors=TICKLINE_COLOR, linewidth=1.5, alpha=1.0, zorder=1)
        ax.text(
            tt,
            -X_AXIS_LABEL_Y_OFFSET,
            tt.strftime("%H:%M"),
            transform=ax.get_xaxis_transform(),
            rotation=X_AXIS_LABEL_ROTATION_DEG,
            ha="right",
            va="top",
            fontsize=X_AXIS_LABEL_FONT_SIZE,
            color=AXIS_LABEL_COLOR,
            clip_on=False,
            zorder=10,
            path_effects=xlab_effects,
        )

    ax.margins(x=0)
    fig.subplots_adjust(bottom=X_AXIS_BOTTOM_MARGIN)

    try:
        # Important: save with correct figure background to avoid white edges
        fig.savefig(out_path, facecolor=fig.get_facecolor())
    finally:
        plt.close(fig)
        plt.close("all")
