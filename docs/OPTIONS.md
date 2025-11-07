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

Create multiple independent camera entities with different configurations.

### Price Entity

**Option:** `price_entity_id` | **Type:** String | **Default:** Empty (use Tibber) | **Location:** Setup dialog

Optional sensor entity containing price data. Leave blank to use Tibber integration.

> [!TIP]
> The data source can be changed using the `tibber_graph.set_data_source` action (see [README.md](README.md#actions)).

### Entity Name

**Option:** `entity_name` | **Type:** String | **Default:** Auto-generated | **Location:** Setup dialog

Custom name for this entity. Leave blank for automatic. Must be unique.

## General Settings

### Theme

**Option:** `theme` | **Type:** Select | **Options:** `dark`, `light` | **Default:** `dark`

Visual theme for colors.

### Transparent Background

**Option:** `transparent_background` | **Type:** Boolean | **Default:** `false`

Use transparent background with selected theme.

### Canvas Width

**Option:** `canvas_width` | **Type:** Integer | **Default:** `1180` | **Unit:** pixels

Width of rendered graph.

### Canvas Height

**Option:** `canvas_height` | **Type:** Integer | **Default:** `820` | **Unit:** pixels

Height of rendered graph.

### Force Fixed Size

**Option:** `force_fixed_size` | **Type:** Boolean | **Default:** `true`

Always render at configured canvas size.

### Cheap Price Points

**Option:** `cheap_price_points` | **Type:** Integer | **Default:** `0`

Number of lowest-price periods to highlight per day (0 = none). Works with `cheap_price_threshold`.

### Cheap Price Threshold

**Option:** `cheap_price_threshold` | **Type:** Float | **Default:** `0.0`

Price threshold for highlighting cheap periods (0 = disabled). Works with `cheap_price_points`.

## X-axis Settings

### Show X-axis Ticks

**Option:** `show_x_ticks` | **Type:** Boolean | **Default:** `false`

Show tick marks on X-axis.

### Show Cheap Periods on X-axis

**Option:** `cheap_price_on_x_axis` | **Type:** Boolean | **Default:** `false`

Show cheap period start/end times on X-axis.

### Start Graph At

**Option:** `start_graph_at` | **Type:** Select | **Options:** `midnight`, `current_hour`, `show_all` | **Default:** `show_all`

Starting point: **Midnight**, **Current hour**, or **Show all** available data.

### X-axis Tick Step

**Option:** `x_tick_step_hours` | **Type:** Integer | **Default:** `3` | **Unit:** hours

Hours between each time label.

### Hours to Show

**Option:** `hours_to_show` | **Type:** Integer or empty | **Default:** Empty (all data) | **Unit:** hours

Number of hours to display from start point. Leave empty for all available data.

### Show Vertical Grid

**Option:** `show_vertical_grid` | **Type:** Boolean | **Default:** `true`

Show vertical gridlines.

## Y-axis Settings

### Show Y-axis

**Option:** `show_y_axis` | **Type:** Boolean | **Default:** `true`

Show Y-axis with ticks, labels, and spine.

### Show Y-axis Ticks

**Option:** `show_y_axis_ticks` | **Type:** Boolean | **Default:** `false`

Show tick marks on Y-axis.

### Show Horizontal Grid

**Option:** `show_horizontal_grid` | **Type:** Boolean | **Default:** `false`

Show horizontal gridlines.

### Show Average Price Line

**Option:** `show_average_price_line` | **Type:** Boolean | **Default:** `true`

Show dotted line at average price level.

### Y-axis Label Rotation

**Option:** `y_axis_label_rotation_deg` | **Type:** Integer | **Default:** `0` | **Unit:** degrees

Rotation angle for Y-axis labels.

### Y-axis Side

**Option:** `y_axis_side` | **Type:** `left` or `right` | **Default:** `left`

Display Y-axis on left or right side.

### Y-axis Tick Count

**Option:** `y_tick_count` | **Type:** Integer or empty | **Default:** Empty (automatic)

Number of ticks on Y-axis. Leave empty for automatic.

### Y-axis Tick Use Colors

**Option:** `y_tick_use_colors` | **Type:** Boolean | **Default:** `false`

Color Y-axis tick labels based on price levels.

## Price Label Settings

### Use Hourly Prices

**Option:** `use_hourly_prices` | **Type:** Boolean | **Default:** `false`

Aggregate to hourly averages.

### Use Cents

**Option:** `use_cents` | **Type:** Boolean | **Default:** `false`

Display prices in cents.

### Currency Override

**Option:** `currency_override` | **Type:** String or empty | **Default:** Empty (auto)

Override currency symbol. Leave empty for automatic.

### Label Current Price

**Option:** `label_current` | **Type:** Boolean | **Default:** `true`

Show current price label.

### Label Current in Header

**Option:** `label_current_in_header` | **Type:** Boolean | **Default:** `true`

Display current price in header instead of on graph.

### Label Current in Header More

**Option:** `label_current_in_header_more` | **Type:** Boolean | **Default:** `true`

Show additional info in header (average and percentage).

### Label Font Size

**Option:** `label_font_size` | **Type:** Integer | **Default:** `11` | **Unit:** points

Font size for all labels.

### Label Maximum Price

**Option:** `label_max` | **Type:** Boolean | **Default:** `true`

Show maximum price label.

### Label Minimum Price

**Option:** `label_min` | **Type:** Boolean | **Default:** `true`

Show minimum price label.

### Label Min/Max Show Price

**Option:** `label_minmax_show_price` | **Type:** Boolean | **Default:** `true`

Show price value on min/max labels.

### Label Show Currency

**Option:** `label_show_currency` | **Type:** Boolean | **Default:** `true`

Show currency symbol on price labels.

### Label Use Colors

**Option:** `label_use_colors` | **Type:** Boolean | **Default:** `false`

Color min/max labels green/red.

### Price Decimals

**Option:** `price_decimals` | **Type:** Integer or empty | **Default:** Empty (auto)

Number of decimal places for prices. Leave empty for automatic.

### Color Price Line by Average

**Option:** `color_price_line_by_average` | **Type:** Boolean | **Default:** `true`

Color price line based on average price with gradients.

## Auto-refresh Settings

### Auto-refresh Enabled

**Option:** `auto_refresh_enabled` | **Type:** Boolean | **Default:** `false`

Automatically refresh graph at regular intervals.

## Resetting Options to Default

### Using the UI

Reset specific options to defaults:

1. Go to **Settings → Devices & services → Tibber Graph → [Entity Name] ⋮**
2. Select **Reconfigure**
3. Check boxes for options to reset
4. Click **Submit**

### Using Actions

Use the [`tibber_graph.reset_option` action](README.md#actions) to reset options programmatically.
