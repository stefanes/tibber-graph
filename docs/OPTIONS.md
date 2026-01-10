# Configuration Options

This document provides a comprehensive reference for all configurable options available through the Home Assistant UI (**[Settings → Devices & services → Tibber Graph](https://my.home-assistant.io/redirect/integration/?domain=tibber_graph) → [Entity Name] ⚙**) and the [provided actions](/README.md#actions).

## Table of Contents

- [General Settings](#general-settings)
- [Price Labels](#price-labels)
- [X-axis Settings](#x-axis-settings)
- [Y-axis Settings](#y-axis-settings)
- [Refresh Settings](#refresh-settings)
- [Resetting Options to Default](#resetting-options-to-default)

### Price entity

**Option:** `price_entity_id` │ **Type:** String • **Default:** Empty (use Tibber)

Optional sensor entity containing price data. Leave blank to use Tibber integration.

> [!TIP]
> The data source can be changed using the [`set_data_source` action](/README.md#tibber_graphset_data_source).

### Entity name

**Option:** `entity_name` │ **Type:** String • **Default:** Auto-generated

Custom name for this entity. Leave blank for automatic. Must be unique.

## General Settings

### Theme

**Option:** `theme` │ **Type:** Select • **Options:** `dark`, `light` • **Default:** `dark`

Visual theme for colors.

### Transparent background

**Option:** `transparent_background` │ **Type:** Boolean • **Default:** `false`

Use transparent background with selected theme.

### Canvas width

**Option:** `canvas_width` │ **Type:** Integer • **Default:** `1180` • **Unit:** pixels

Width of rendered graph.

### Canvas height

**Option:** `canvas_height` │ **Type:** Integer • **Default:** `820` • **Unit:** pixels

Height of rendered graph.

### Force fixed size

**Option:** `force_fixed_size` │ **Type:** Boolean • **Default:** `true`

Always render at configured canvas size.

### Label font size

**Option:** `label_font_size` │ **Type:** Integer • **Default:** `11` • **Unit:** points

Font size for all labels.

### Start graph at

**Option:** `start_graph_at` │ **Type:** Select • **Options:** `midnight`, `current_hour`, `show_all` • **Default:** `show_all`

Starting point: **Midnight**, **Current hour**, or **Show all** available data.

### Hours to show

**Option:** `hours_to_show` │ **Type:** Integer or empty • **Default:** Empty (all data) • **Unit:** hours

Number of hours to display from start point. Leave empty for all available data.

### Cheap price points to highlight

**Option:** `cheap_price_points` │ **Type:** Integer • **Default:** `0`

Number of lowest-price periods to highlight per day (0 = none). Works with `cheap_price_threshold`.

### Cheap price threshold

**Option:** `cheap_price_threshold` │ **Type:** Float • **Default:** `0.0`

Price threshold for highlighting cheap periods (0 = disabled). Works with `cheap_price_points`.

### Show average price line

**Option:** `show_average_price_line` │ **Type:** Boolean • **Default:** `true`

Show line at average price level. See [CUSTOM_THEME.md](docs/CUSTOM_THEME.md#theme-properties) for styling.

### Show cheap price line

**Option:** `show_cheap_price_line` │ **Type:** Boolean • **Default:** `false`

Show line at cheap price threshold level if `cheap_price_threshold` is set. See [CUSTOM_THEME.md](docs/CUSTOM_THEME.md#theme-properties) for styling.

> [!NOTE]
> This option is only available when using using the [`create_graph`](/README.md#tibber_graphcreate_graph) or [`set_option`](/README.md#tibber_graphset_option) actions.

### Color price line by average

**Option:** `color_price_line_by_average` │ **Type:** Boolean • **Default:** `true`

Color price line based on average price with gradients.

## Price Labels

### Number of price decimals

**Option:** `price_decimals` │ **Type:** Integer or empty • **Default:** Empty (auto)

Number of decimal places for prices. Leave empty for automatic.

### Aggregate to hourly prices

**Option:** `use_hourly_prices` │ **Type:** Boolean • **Default:** `false`

Aggregate to hourly averages.

### Display in cents

**Option:** `use_cents` │ **Type:** Boolean • **Default:** `false`

Display prices in cents.

### Currency override

**Option:** `currency_override` │ **Type:** String or empty • **Default:** Empty (auto)

Override currency symbol. Leave empty for automatic detection.

Automatic currency detection (in order of precedence):

1. **Tibber Integration**: If using Tibber as the data source, the currency from your Tibber home is used
2. **Price Sensor - `currency` attribute**: If using a price sensor with a `currency` attribute, that value is used
3. **Price Sensor - `unit_of_measurement`**: If using a price sensor with a `unit_of_measurement` attribute (e.g., `€/kWh`), the currency is extracted from it
4. **Default**: Falls back to `€` if no currency can be determined

> [!NOTE]
> When `use_cents` is enabled, automatic detection will always use `¢` unless an override is specified.

### Show currency on labels

**Option:** `label_show_currency` │ **Type:** Boolean • **Default:** `true`

Show currency symbol on price labels.

> [!NOTE]
> This option is only available when using using the [`create_graph`](/README.md#tibber_graphcreate_graph) or [`set_option`](/README.md#tibber_graphset_option) actions.

### Show current price

**Option:** `label_current` │ **Type:** Dropdown • **Default:** `on`

Show current price:

- `on`: Show in header
- `on_current_price_only`: Show in header with current price only (no average price info)
- `on_in_graph`: Show in graph with price label
- `on_in_graph_no_price`: Show marker dot in graph without price label
- `on_in_graph_no_time`: Show in graph with price label without time information
- `on_in_graph_only_marker`: Show marker dot in graph only (no price or time label)
- `off`: Do not show current price

### Show min price

**Option:** `label_min` │ **Type:** Dropdown • **Default:** `on`

Show minimum price label:

- `on` - Show label with price
- `on_no_price` - Show label without price (time only)
- `on_no_time` - Show label without time (price only)
- `on_only_marker` - Show marker only (no price or time label)
- `off` - Do not show label

### Show max price

**Option:** `label_max` │ **Type:** Dropdown • **Default:** `on`

Show maximum price label:

- `on` - Show label with price
- `on_no_price` - Show label without price (time only)
- `on_no_time` - Show label without time (price only)
- `on_only_marker` - Show marker only (no price or time label)
- `off` - Do not show label

### Use colors on labels

**Option:** `label_use_colors` │ **Type:** Boolean • **Default:** `false`

Color min/max labels.

> [!NOTE]
> This option is only available when using using the [`create_graph`](/README.md#tibber_graphcreate_graph) or [`set_option`](/README.md#tibber_graphset_option) actions.

### Show min/max per day

**Option:** `label_minmax_per_day` │ **Type:** Select • **Options:** `on`, `on_from_today`, `off` • **Default:** `on`

Controls how minimum and maximum price labels are displayed:

- `on` - Show minimum and maximum price labels for each day in the graph
- `on_from_today` - Show minimum and maximum price labels from today forward only (yesterday's min/max not shown)
- `off` - Show a single min/max for the entire visible range

## X-axis Settings

### Show X-axis

**Option:** `show_x_axis` │ **Type:** Select • **Options:** `on`, `on_with_tick_marks`, `off` • **Default:** `on`

X-axis visibility:

- `on` - Show axis/labels without tick marks
- `on_with_tick_marks` - Show axis/labels with tick marks
- `off` - Hide completely

### X-axis tick interval

**Option:** `x_tick_step_hours` │ **Type:** Integer • **Default:** `3` • **Unit:** hours

Hours between each time label.

### Highlight cheap periods on X-axis

**Option:** `cheap_periods_on_x_axis` │ **Type:** Select • **Options:** `on`, `on_comfy`, `on_compact`, `off` • **Default:** `off`

Highlight cheap periods on X-axis with different display modes:

- `on` - Highlight cheap hours using only the existing X-axis labels (color existing labels if they fall in cheap periods)
- `on_comfy` - Show cheap period boundaries in a separate row below regular time labels (comfortable multi-line layout)
- `on_compact` - Show cheap period boundaries on the same row as regular time labels (compact single-line layout, removes conflicting regular labels)
- `off` - Do not highlight cheap periods on X-axis

This option requires either `cheap_price_points` or `cheap_price_threshold` to be configured to identify cheap periods.

### Highlight cheap period boundaries

**Option:** `cheap_boundary_highlight` │ **Type:** Select • **Options:** `none`, `underline`, `underline_all` • **Default:** `none`

Highlight start and end time labels of cheap periods with different underline styles:

- `none` - Do not highlight cheap period boundaries
- `underline` - Underline cheap period boundaries on first row only
- `underline_all` - Underline all cheap period boundaries

This option requires `cheap_periods_on_x_axis` and either `cheap_price_points` or `cheap_price_threshold` to be configured to identify cheap periods.

> [!NOTE]
> This option is only available when using using the [`create_graph`](/README.md#tibber_graphcreate_graph) or [`set_option`](/README.md#tibber_graphset_option) actions.

### Show vertical grid

**Option:** `show_vertical_grid` │ **Type:** Boolean • **Default:** `true`

Show vertical gridlines.

## Y-axis Settings

### Show Y-axis

**Option:** `show_y_axis` │ **Type:** Dropdown • **Default:** `on`

Y-axis visibility with three options:

- `on` - Show axis, labels, and spine (no tick marks)
- `on_with_tick_marks` - Show axis, labels, spine, and tick marks
- `off` - Hide Y-axis completely

### Number of Y-axis ticks

**Option:** `y_tick_count` │ **Type:** Integer or empty • **Default:** Empty (automatic)

Number of ticks on Y-axis. Leave empty for automatic.

### Y-axis label rotation

**Option:** `y_axis_label_rotation_deg` │ **Type:** Integer • **Default:** `0` • **Unit:** degrees

Rotation angle for Y-axis labels.

### Y-axis position

**Option:** `y_axis_side` │ **Type:** `left` or `right` • **Default:** `left`

Display Y-axis on left or right side.

### Use colors on Y-axis tick labels

**Option:** `y_tick_use_colors` │ **Type:** Boolean • **Default:** `false`

Color Y-axis tick labels based on price levels.

> [!NOTE]
> This option is only available when using using the [`create_graph`](/README.md#tibber_graphcreate_graph) or [`set_option`](/README.md#tibber_graphset_option) actions.

### Show horizontal grid

**Option:** `show_horizontal_grid` │ **Type:** Boolean • **Default:** `false`

Show horizontal gridlines.

## Refresh Settings

### Refresh mode

**Option:** `refresh_mode` │ **Type:** Dropdown • **Default:** `system`

Control when the graph is refreshed:

- `system` (default): Updated by system only
- `system_interval`: Updated by system & on interval
- `interval`: Updated on interval only (every 15 minutes for 15-min pricing, every hour for hourly pricing)
- `sensor`: Updated when data source sensor changes (requires [price sensor as data source](/README.md#price-sensors-as-data-source))
- `manual`: Manual updates using [`render` action](/README.md#tibber_graphrender) only (no automatic refresh)

| Mode              | Updated by system | Updated on interval | Updated by sensor | Manual updates |
| ----------------- | ----------------- | ------------------- | ----------------- | -------------- |
| `system`          | Yes               | No                  | No                | Yes            |
| `system_interval` | Yes               | Yes                 | No                | Yes            |
| `interval`        | No                | Yes                 | No                | Yes            |
| `sensor`          | No                | No                  | Yes               | Yes            |
| `manual`          | No                | No                  | No                | Yes            |

> [!NOTE]
> The `sensor` refresh mode is **only applicable when using a price sensor as data source**. If data source is the Tibber integration, `refresh_mode` will be reverted to `system`.

### Show data source name

**Option:** `show_data_source_name` │ **Type:** Boolean • **Default:** `false`

Show the data source friendly name in the graph footer.

> [!NOTE]
> This option is only available when using using the [`create_graph`](/README.md#tibber_graphcreate_graph) or [`set_option`](/README.md#tibber_graphset_option) actions.

## Resetting Options to Default

### Using the UI

Reset specific options to defaults:

1. Go to **[Settings → Devices & services → Tibber Graph](https://my.home-assistant.io/redirect/integration/?domain=tibber_graph) → [Entity Name] ⋮**
2. Select **Reconfigure**
3. Check options to reset
4. Click **Submit**

### Using Actions

Use the [`reset_option` action](/README.md#tibber_graphreset_option) to reset options programmatically.
