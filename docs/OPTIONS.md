# Configuration Options

This document provides a comprehensive reference for all configurable options available through the Home Assistant UI (**[Settings → Devices & services → Tibber Graph](https://my.home-assistant.io/redirect/integration/?domain=tibber_graph) → [Entity Name] ⚙**) and the [provided actions](/README.md#actions).

## Table of Contents

- [Multiple Entity Support](#multiple-entity-support)
- [General Settings](#general-settings)
- [Price Labels](#price-labels)
- [X-axis Settings](#x-axis-settings)
- [Y-axis Settings](#y-axis-settings)
- [Refresh Settings](#refresh-settings)
- [Resetting Options to Default](#resetting-options-to-default)

## Multiple Entity Support

Create multiple independent camera entities with different configurations.

### Price Entity

**Option:** `price_entity_id` │ **Type:** String • **Default:** Empty (use Tibber)

Optional sensor entity containing price data. Leave blank to use Tibber integration.

> [!TIP]
> The data source can be changed using the [`tibber_graph.set_data_source` action](/README.md#tibber_graphset_data_source) (see [README.md](/README.md#actions)).

### Entity Name

**Option:** `entity_name` │ **Type:** String • **Default:** Auto-generated

Custom name for this entity. Leave blank for automatic. Must be unique.

## General Settings

### Theme

**Option:** `theme` │ **Type:** Select • **Options:** `dark`, `light` • **Default:** `dark`

Visual theme for colors.

### Transparent Background

**Option:** `transparent_background` │ **Type:** Boolean • **Default:** `false`

Use transparent background with selected theme.

### Canvas Width

**Option:** `canvas_width` │ **Type:** Integer • **Default:** `1180` • **Unit:** pixels

Width of rendered graph.

### Canvas Height

**Option:** `canvas_height` │ **Type:** Integer • **Default:** `820` • **Unit:** pixels

Height of rendered graph.

### Force Fixed Size

**Option:** `force_fixed_size` │ **Type:** Boolean • **Default:** `true`

Always render at configured canvas size.

### Label Font Size

**Option:** `label_font_size` │ **Type:** Integer • **Default:** `11` • **Unit:** points

Font size for all labels.

### Start Graph At

**Option:** `start_graph_at` │ **Type:** Select • **Options:** `midnight`, `current_hour`, `show_all` • **Default:** `show_all`

Starting point: **Midnight**, **Current hour**, or **Show all** available data.

### Hours to Show

**Option:** `hours_to_show` │ **Type:** Integer or empty • **Default:** Empty (all data) • **Unit:** hours

Number of hours to display from start point. Leave empty for all available data.

### Cheap Price Points

**Option:** `cheap_price_points` │ **Type:** Integer • **Default:** `0`

Number of lowest-price periods to highlight per day (0 = none). Works with `cheap_price_threshold`.

### Cheap Price Threshold

**Option:** `cheap_price_threshold` │ **Type:** Float • **Default:** `0.0`

Price threshold for highlighting cheap periods (0 = disabled). Works with `cheap_price_points`.

### Show Average Price Line

**Option:** `show_average_price_line` │ **Type:** Boolean • **Default:** `true`

Show dotted line at average price level.

### Color Price Line by Average

**Option:** `color_price_line_by_average` │ **Type:** Boolean • **Default:** `true`

Color price line based on average price with gradients.

## Price Labels

### Price Decimals

**Option:** `price_decimals` │ **Type:** Integer or empty • **Default:** Empty (auto)

Number of decimal places for prices. Leave empty for automatic.

### Use Hourly Prices

**Option:** `use_hourly_prices` │ **Type:** Boolean • **Default:** `false`

Aggregate to hourly averages.

### Use Cents

**Option:** `use_cents` │ **Type:** Boolean • **Default:** `false`

Display prices in cents.

### Currency Override

**Option:** `currency_override` │ **Type:** String or empty • **Default:** Empty (auto)

Override currency symbol. Leave empty for automatic detection.

Automatic currency detection (in order of precedence):

1. **Tibber Integration**: If using Tibber as the data source, the currency from your Tibber home is used
2. **Custom Sensor - `currency` attribute**: If using a custom sensor with a `currency` attribute, that value is used
3. **Custom Sensor - `unit_of_measurement`**: If using a custom sensor with a `unit_of_measurement` attribute (e.g., `€/kWh`), the currency is extracted from it
4. **Default**: Falls back to `€` if no currency can be determined

> [!NOTE]
> When `use_cents` is enabled, automatic detection uses `¢` unless an override is specified.

### Label Show Currency

**Option:** `label_show_currency` │ **Type:** Boolean • **Default:** `true`

Show currency symbol on price labels.

### Show Current Price

**Option:** `label_current` │ **Type:** Dropdown • **Default:** `on`

Show current price:

- `on`: Show in header
- `on_current_price_only`: Show in header with current price only (no average price info)
- `on_in_graph`: Show in graph with price label
- `on_in_graph_no_price`: Show marker dot in graph without price label
- `off`: Do not show current price

### Label Minimum Price

**Option:** `label_min` │ **Type:** Dropdown • **Default:** `on`

Show minimum price label:

- `on` - Show label with price
- `on_no_price` - Show label without price (time only)
- `off` - Do not show label

### Label Maximum Price

**Option:** `label_max` │ **Type:** Dropdown • **Default:** `on`

Show maximum price label:

- `on` - Show label with price
- `on_no_price` - Show label without price (time only)
- `off` - Do not show label

### Label Use Colors

**Option:** `label_use_colors` │ **Type:** Boolean • **Default:** `false`

Color min/max labels.

## X-axis Settings

### Show X-axis

**Option:** `show_x_axis` │ **Type:** Select • **Options:** `on`, `on_with_tick_marks`, `off` • **Default:** `on`

X-axis visibility:

- `on` - Show axis/labels without tick marks
- `on_with_tick_marks` - Show axis/labels with tick marks
- `off` - Hide completely

### X-axis Tick Step

**Option:** `x_tick_step_hours` │ **Type:** Integer • **Default:** `3` • **Unit:** hours

Hours between each time label.

### Highlight Cheap Periods on X-axis

**Option:** `cheap_periods_on_x_axis` │ **Type:** Select • **Options:** `on`, `on_comfy`, `on_compact`, `off` • **Default:** `off`

Highlight cheap periods on X-axis with different display modes:

- `on` - Highlight cheap hours using only the existing X-axis labels (color existing labels if they fall in cheap periods)
- `on_comfy` - Show cheap period boundaries in a separate row below regular time labels (comfortable multi-line layout)
- `on_compact` - Show cheap period boundaries on the same row as regular time labels (compact single-line layout, removes conflicting regular labels)
- `off` - Do not highlight cheap periods on X-axis

This option requires either `cheap_price_points` or `cheap_price_threshold` to be configured to identify cheap periods.

### Show Vertical Grid

**Option:** `show_vertical_grid` │ **Type:** Boolean • **Default:** `true`

Show vertical gridlines.

## Y-axis Settings

### Show Y-axis

**Option:** `show_y_axis` │ **Type:** Dropdown • **Default:** `on`

Y-axis visibility with three options:

- `on` - Show axis, labels, and spine (no tick marks)
- `on_with_tick_marks` - Show axis, labels, spine, and tick marks
- `off` - Hide Y-axis completely

### Y-axis Tick Count

**Option:** `y_tick_count` │ **Type:** Integer or empty • **Default:** Empty (automatic)

Number of ticks on Y-axis. Leave empty for automatic.

### Y-axis Label Rotation

**Option:** `y_axis_label_rotation_deg` │ **Type:** Integer • **Default:** `0` • **Unit:** degrees

Rotation angle for Y-axis labels.

### Y-axis Side

**Option:** `y_axis_side` │ **Type:** `left` or `right` • **Default:** `left`

Display Y-axis on left or right side.

### Y-axis Tick Use Colors

**Option:** `y_tick_use_colors` │ **Type:** Boolean • **Default:** `false`

Color Y-axis tick labels based on price levels.

### Show Horizontal Grid

**Option:** `show_horizontal_grid` │ **Type:** Boolean • **Default:** `false`

Show horizontal gridlines.

## Refresh Settings

### Refresh Mode

**Option:** `refresh_mode` │ **Type:** Dropdown • **Default:** `system`

Control when the graph is refreshed:

- `system` (default): Updated by system only
- `system_interval`: Updated by system & on interval
- `interval`: Updated on interval only (every 15 minutes for 15-min pricing, every hour for hourly pricing)
- `manual`: Manual updates using [`tibber_graph.render` action](/README.md#actions) only (no automatic refresh)

| Mode              | Update on interval | Updated by system | Manual update |
| ----------------- | ------------------ | ----------------- | ------------- |
| `system`          | No                 | Yes               | Yes           |
| `system_interval` | Yes                | Yes               | Yes           |
| `interval`        | Yes                | No                | Yes           |
| `manual`          | No                 | No                | Yes           |

## Resetting Options to Default

### Using the UI

Reset specific options to defaults:

1. Go to **[Settings → Devices & services → Tibber Graph](https://my.home-assistant.io/redirect/integration/?domain=tibber_graph) → [Entity Name] ⋮**
2. Select **Reconfigure**
3. Check options to reset
4. Click **Submit**

### Using Actions

Use the [`tibber_graph.reset_option` action](/README.md#actions) to reset options programmatically.
