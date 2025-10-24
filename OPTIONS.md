# Tibber Graph - Configuration Options

This document provides a comprehensive reference for all configurable options available through the Home Assistant UI (Settings → Devices & Services → Tibber Graph → Configure).

## Table of Contents

- [General Settings](#general-settings)
- [X-axis Settings](#x-axis-settings)
- [Y-axis Settings](#y-axis-settings)
- [Price Label Settings](#price-label-settings)
- [Auto-refresh Settings](#auto-refresh-settings)
- [Resetting Options to Default](#resetting-options-to-default)

## General Settings

### Theme

**Option:** `theme`
**Type:** Selection (`light` or `dark`)
**Default:** `dark`

Selects the visual theme for the graph. The theme affects colors for background, grid, labels, and price lines.

- **light**: Bright background with dark text, suitable for display in well-lit areas
- **dark**: Dark background with light text, suitable for OLED displays and low-light environments

### Canvas Width

**Option:** `canvas_width`
**Type:** Integer (positive)
**Default:** `1200`
**Unit:** pixels

The width of the rendered graph image. Larger values provide more detail but increase file size.

### Canvas Height

**Option:** `canvas_height`
**Type:** Integer (positive)
**Default:** `700`
**Unit:** pixels

The height of the rendered graph image. Larger values provide more detail but increase file size.

### Force Fixed Size

**Option:** `force_fixed_size`
**Type:** Boolean
**Default:** `true`

When enabled, the graph always renders at the configured canvas width and height, ignoring Home Assistant's camera size requests. When disabled, the graph may be resized based on where it's displayed.

## X-axis Settings

### Show X-axis Ticks

**Option:** `show_x_ticks`
**Type:** Boolean
**Default:** `true`

Controls whether tick marks are displayed on the X-axis at label positions.

### Start at Midnight

**Option:** `start_at_midnight`
**Type:** Boolean
**Default:** `true`

Controls the time range displayed on the graph:

- **true**: Shows prices from midnight to midnight (full day view)
- **false**: Shows prices from the current hour to the last available data point

### X-axis Label Rotation

**Option:** `x_axis_label_rotation_deg`
**Type:** Integer
**Default:** `45`
**Unit:** degrees

Controls the rotation angle of X-axis time labels:

- `0`: Horizontal labels
- `45`: Diagonal labels (default, saves space)
- `90`: Vertical labels
- Custom angles: Any integer value between 0-360

### X-axis Tick Step (Hours)

**Option:** `x_tick_step_hours`
**Type:** Integer (positive)
**Default:** `3`
**Unit:** hours

Interval between X-axis time labels. For example:

- `1`: Label every hour
- `3`: Label every 3 hours (default)
- `6`: Label every 6 hours

### Hours to Show

**Option:** `hours_to_show`
**Type:** Integer (positive) or empty
**Default:** Empty (show all available data)
**Unit:** hours

Limits the graph to display only a specific number of hours from the start time. The start time is determined by the "Start at Midnight" setting:

- When **"Start at Midnight"** is enabled: Shows from midnight (00:00) up to the specified number of hours or the last available data point, whichever comes first
- When **"Start at Midnight"** is disabled: Shows from one hour before the current time up to the specified number of hours or the last available data point, whichever comes first

When left empty (default), the graph shows all available data without a time limit:

- **Midnight mode**: Full 24-hour period from midnight to midnight
- **Current mode**: From one hour before current time to the last available data point

This option works correctly with both 15-minute and hourly pricing data.

**Examples:**

- `6`: Shows the next 6 hours from the start time
- `12`: Shows the next 12 hours from the start time
- `24`: Shows the next 24 hours from the start time
- Empty: Shows all available data (default behavior)

## Y-axis Settings

### Show Y-axis

**Option:** `show_y_axis`
**Type:** Boolean
**Default:** `true`

Controls whether the Y-axis is displayed (including ticks, labels, and spine). Set to `false` to hide the entire Y-axis.

### Show Y-axis Grid

**Option:** `show_y_grid`
**Type:** Boolean
**Default:** `true`

Controls whether horizontal gridlines are displayed across the graph at Y-axis tick positions.

### Y-axis Label Rotation

**Option:** `y_axis_label_rotation_deg`
**Type:** Integer
**Default:** `0`
**Unit:** degrees

Controls the rotation angle of Y-axis tick labels:

- `0`: Horizontal labels (default)
- `90`: Vertical labels for left-side Y-axis (reads bottom-to-top)
- `270`: Vertical labels for right-side Y-axis (reads top-to-bottom)
- Custom angles: Any integer value between 0-360

### Y-axis Side

**Option:** `y_axis_side`
**Type:** Selection (`left` or `right`)
**Default:** `left`

Controls which side of the graph the Y-axis appears on.

### Y-axis Tick Count

**Option:** `y_tick_count`
**Type:** Integer (positive) or empty
**Default:** Empty (automatic)

Controls the number of ticks on the Y-axis. When left empty, the number of ticks is determined automatically based on the price range. You can specify a value (e.g., 3, 5, 7) to control exactly how many ticks appear on the Y-axis.

### Y-axis Tick Use Colors

**Option:** `y_tick_use_colors`
**Type:** Boolean
**Default:** `false`

When enabled, colors Y-axis tick labels based on price levels:

- **Green**: Minimum price
- **Amber**: Average price
- **Red**: Maximum price

## Price Label Settings

### Use Hourly Prices

**Option:** `use_hourly_prices`
**Type:** Boolean
**Default:** `false`

When enabled, aggregates 15-minute price data into hourly averages (4 quarters per hour). Useful for displaying smoother graphs when Tibber provides 15-minute interval data.

### Use Cents

**Option:** `use_cents`
**Type:** Boolean
**Default:** `false`

When enabled, displays prices in cents (multiplies by 100). For example, 0.25 EUR becomes 25¢. The currency label automatically changes to "¢" unless a `currency_override` is explicitly set.

### Currency Override

**Option:** `currency_override`
**Type:** String
**Default:** `null` (auto: Tibber home currency for standard mode, "¢" for cents mode)

Overrides the currency symbol displayed on labels. Examples: `EUR`, `SEK`, `öre`, `¢`. When not set:

- **Standard mode** (`use_cents=false`): Uses the currency from your Tibber home configuration
- **Cents mode** (`use_cents=true`): Automatically uses "¢" as the currency label

### Label Current Price

**Option:** `label_current`
**Type:** Boolean
**Default:** `true`

When enabled, displays a label for the current price on the graph.

### Label Current at Top

**Option:** `label_current_at_top`
**Type:** Boolean
**Default:** `false`

Controls the position of the current price label:

- **true**: Display at the top-left corner of the graph
- **false**: Display on the graph at the current time position

### Label Font Size

**Option:** `label_font_size`
**Type:** Integer (positive)
**Default:** `11`
**Unit:** points

Font size for all labels on the graph (X-axis time labels, Y-axis price labels, and in-graph price labels for min/max/current when not at top).

### Label Maximum Price

**Option:** `label_max`
**Type:** Boolean
**Default:** `true`

When enabled, displays a label for the maximum price on the graph.

### Label Minimum Price

**Option:** `label_min`
**Type:** Boolean
**Default:** `true`

When enabled, displays a label for the minimum price on the graph.

### Label Min/Max Show Price

**Option:** `label_minmax_show_price`
**Type:** Boolean
**Default:** `true`

Controls what information is shown on min/max labels:

- **true**: Show both time and price (e.g., "08:00 - 0.25 EUR")
- **false**: Show only time (e.g., "08:00")

### Label Show Currency

**Option:** `label_show_currency`
**Type:** Boolean
**Default:** `true`

When enabled, displays the currency symbol on all price labels (minimum, maximum, and current).

### Label Use Colors

**Option:** `label_use_colors`
**Type:** Boolean
**Default:** `false`

When enabled, colors the min/max/current price labels:

- **Green**: Minimum price
- **Amber**: Current/average price
- **Red**: Maximum price

### Price Decimals

**Option:** `price_decimals`
**Type:** Integer (positive) or None
**Default:** `None` (auto: `2` for standard prices, `0` for cents)

Number of decimal places to display for all prices. When set to `None` (default), the decimals are automatically chosen based on the `use_cents` setting.

Examples:

- `None`: Auto-selects 2 decimals for standard prices (0.25 SEK) or 0 decimals for cents (25 öre)
- `0`: Shows 1 (no decimals)
- `2`: Shows 0.25 or 25.00 (explicit 2 decimals regardless of cents mode)
- `3`: Shows 0.251 or 25.100

## Auto-refresh Settings

### Auto-refresh Enabled

**Option:** `auto_refresh_enabled`
**Type:** Boolean
**Default:** `false`

When enabled, the graph automatically refreshes at regular intervals to show updated price data. The refresh interval is fixed at 10 minutes and is not configurable through the UI.

## Resetting Options to Default

Some options support being reset to their default values when you need to restore automatic behavior. These options include:

- **Hours to show**: Resets to showing all available data
- **Y-axis tick count**: Resets to automatic tick calculation
- **Price decimals**: Resets to automatic decimal places (2 for standard, 0 for cents)
- **Currency override**: Resets to automatic currency (Tibber home currency or '¢')

### How to Reset Options

Due to a limitation in the Home Assistant UI, nullable number fields cannot be cleared back to empty/automatic once a value has been set using the regular Options dialog.

To reset these options to their defaults:

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Find the **Tibber Graph** integration
3. Click the three-dot menu (⋮) on the integration card
4. Select **Reconfigure**
5. Check the boxes for the options you want to reset to default
6. Click **Submit**

Only the options you check will be reset. All other settings will remain unchanged.
