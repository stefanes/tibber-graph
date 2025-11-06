# Configuration Options

This document provides a comprehensive reference for all configurable options available through the Home Assistant UI (**Settings → Devices & services → Tibber Graph → [Entity Name] ⚙**) and the [provided actions](README.md#actions).

## Table of Contents

- [Multiple Entity Support](#multiple-entity-support)
- [General Settings](#general-settings)
- [X-axis Settings](#x-axis-settings)
- [Y-axis Settings](#y-axis-settings)
- [Price Label Settings](#price-label-settings)
- [Auto-refresh Settings](#auto-refresh-settings)
- [Resetting Options to Default](#resetting-options-to-default)

## Multiple Entity Support

Create multiple independent camera entities with different configurations for different dashboards or purposes.

### Price Entity

**Option:** `price_entity_id` | **Type:** String | **Default:** Empty (use Tibber) | **Location:** Setup dialog

Optional sensor entity containing price data in its `prices` or `data` attribute. Must contain a list of prices with `start_time`|`start`|`startsAt` and `price`|`price_per_kwh`|`total` fields. Leave blank to use the Tibber integration.

> [!TIP]
> The data source can be changed at any time using the `tibber_graph.set_data_source` action (see [README.md](README.md#actions)).

### Entity Name

**Option:** `entity_name` | **Type:** String | **Default:** Auto-generated | **Location:** Setup dialog

Identifies each Tibber Graph instance. Leave blank to auto-generate from price entity friendly name or Tibber home name. Must be unique.

## General Settings

### Theme

**Option:** `theme` | **Type:** Select | **Options:** `dark`, `light` | **Default:** `dark`

Visual theme affecting colors for background, grid, labels, and price lines.

### Transparent Background

**Option:** `transparent_background` | **Type:** Boolean | **Default:** `false`

Use transparent background with the selected theme. When enabled, the background color is transparent for both dark and light themes, useful for OLED displays or custom dashboards.

### Canvas Width

**Option:** `canvas_width` | **Type:** Integer | **Default:** `1180` | **Unit:** pixels

Width of the rendered graph image.

### Canvas Height

**Option:** `canvas_height` | **Type:** Integer | **Default:** `820` | **Unit:** pixels

Height of the rendered graph image.

### Force Fixed Size

**Option:** `force_fixed_size` | **Type:** Boolean | **Default:** `true`

Always render at configured canvas size.

## X-axis Settings

### Show X-axis Ticks

**Option:** `show_x_ticks` | **Type:** Boolean | **Default:** `false`

Show tick marks on the X-axis at label positions.

### Start Graph At

**Option:** `start_graph_at` | **Type:** Select | **Options:** `midnight`, `current_hour`, `show_all` | **Default:** `show_all`

Choose where to start the graph:

- **Midnight**: Start at midnight
- **Current hour**: Start at current hour (an extra hour before is shown for visual continuity but not included in calculations)
- **Show all**: Show all available data from first to last price point

The hours shown also depend on the 'Hours to show' setting. All price calculations (min, max, average) are based on the displayed price data.

### X-axis Tick Step

**Option:** `x_tick_step_hours` | **Type:** Integer | **Default:** `3` | **Unit:** hours

Hours between each time label (e.g., 1 = every hour, 3 = every 3 hours).

### Hours to Show

**Option:** `hours_to_show` | **Type:** Integer or empty | **Default:** Empty (all data) | **Unit:** hours

Number of hours to display from start point. Leave empty to show all available data.

### Show Vertical Grid

**Option:** `show_vertical_grid` | **Type:** Boolean | **Default:** `true`

Show vertical gridlines at X-axis tick positions.

## Y-axis Settings

### Show Y-axis

**Option:** `show_y_axis` | **Type:** Boolean | **Default:** `true`

Show Y-axis with ticks, labels, and spine.

### Show Y-axis Ticks

**Option:** `show_y_axis_ticks` | **Type:** Boolean | **Default:** `false`

Show tick marks on the Y-axis at price levels.

### Show Horizontal Grid

**Option:** `show_horizontal_grid` | **Type:** Boolean | **Default:** `false`

Show horizontal gridlines at Y-axis tick positions.

### Show Average Price Line

**Option:** `show_average_price_line` | **Type:** Boolean | **Default:** `true`

Show dotted line at average price level. The average is calculated from the displayed price data, taking into account filtering options like "Start graph at" and "Hours to show".

### Cheap Price Points

**Option:** `cheap_price_points` | **Type:** Integer | **Default:** `0`

Number of lowest-price periods to highlight per day (0 = none). Past periods are dimmed. Works in combination with `cheap_price_threshold` - always highlights at least N cheapest periods, plus any additional periods below the threshold.

### Cheap Price Threshold

**Option:** `cheap_price_threshold` | **Type:** Float | **Default:** `0.0`

Price threshold below which periods are highlighted as cheap (0 = disabled, e.g., 0.5 = 50 öre). Works in combination with `cheap_price_points` - highlights the N cheapest periods plus any additional periods below this threshold. The threshold is in the same unit as prices.

### Y-axis Label Rotation

**Option:** `y_axis_label_rotation_deg` | **Type:** Integer | **Default:** `0` | **Unit:** degrees

Rotation angle for Y-axis labels (0 = horizontal, 90 = vertical left, 270 = vertical right).

### Y-axis Side

**Option:** `y_axis_side` | **Type:** `left` or `right` | **Default:** `left`

Which side of the graph to display the Y-axis.

### Y-axis Tick Count

**Option:** `y_tick_count` | **Type:** Integer or empty | **Default:** Empty (automatic)

Number of ticks on Y-axis. Leave empty for automatic.

### Y-axis Tick Use Colors

**Option:** `y_tick_use_colors` | **Type:** Boolean | **Default:** `false`

Color Y-axis tick labels (green = min, amber = avg, red = max).

## Price Label Settings

### Use Hourly Prices

**Option:** `use_hourly_prices` | **Type:** Boolean | **Default:** `false`

Aggregate 15-minute data into hourly averages.

### Use Cents

**Option:** `use_cents` | **Type:** Boolean | **Default:** `false`

Display prices in cents (multiplied by 100).

### Currency Override

**Option:** `currency_override` | **Type:** String or empty | **Default:** Empty (auto)

Override currency symbol (e.g., `EUR`, `SEK`, `öre`). Leave empty for automatic.

### Label Current Price

**Option:** `label_current` | **Type:** Boolean | **Default:** `true`

Show current price label on the graph.

### Label Current in Header

**Option:** `label_current_in_header` | **Type:** Boolean | **Default:** `true`

Display current price centered in header (true) or on the graph (false).

### Label Current in Header More

**Option:** `label_current_in_header_more` | **Type:** Boolean | **Default:** `true`

Show additional info in header (average price and % to average) when `label_current_in_header` is enabled. The average and percentage are calculated from the displayed price data.

### Label Font Size

**Option:** `label_font_size` | **Type:** Integer | **Default:** `11` | **Unit:** points

Font size for all labels (X-axis, Y-axis, and in-graph price labels).

### Label Maximum Price

**Option:** `label_max` | **Type:** Boolean | **Default:** `true`

Show maximum price label on the graph. The maximum is determined from the displayed price data.

### Label Minimum Price

**Option:** `label_min` | **Type:** Boolean | **Default:** `true`

Show minimum price label on the graph. The minimum is determined from the displayed price data.

### Label Min/Max Show Price

**Option:** `label_minmax_show_price` | **Type:** Boolean | **Default:** `true`

Show price value on min/max labels (true) or only time (false).

### Label Show Currency

**Option:** `label_show_currency` | **Type:** Boolean | **Default:** `true`

Show currency symbol on price labels.

### Label Use Colors

**Option:** `label_use_colors` | **Type:** Boolean | **Default:** `false`

Color price labels (green = min, amber = current, red = max).

### Price Decimals

**Option:** `price_decimals` | **Type:** Integer or empty | **Default:** Empty (auto)

Number of decimal places for prices. Leave empty for automatic.

### Color Price Line by Average

**Option:** `color_price_line_by_average` | **Type:** Boolean | **Default:** `true`

Color the price line based on average price. Blue for below average, amber for near average (±25%), red for above average. The average is calculated from the displayed price data.

## Auto-refresh Settings

### Auto-refresh Enabled

**Option:** `auto_refresh_enabled` | **Type:** Boolean | **Default:** `false`

Automatically refresh the graph every 10 minutes.

## Resetting Options to Default

Options can be reset to their default values in two ways:

### Using the UI

Some options (Hours to show, Y-axis tick count, Price decimals, Currency override) can be reset to their default automatic behavior:

1. Go to **Settings → Devices & services → Tibber Graph → [Entity Name] ⋮**
2. Select **Reconfigure**
3. Check the boxes for options to reset
4. Click **Submit**

### Using Actions

You can also reset options programmatically using the [`tibber_graph.reset_option` action](README.md#actions). This action allows you to:

- Reset specific options by providing a list of option names
- Reset all options at once by omitting the options parameter or providing an empty list
