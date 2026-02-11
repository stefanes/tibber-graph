<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

## [0.7.3] - 2026-02-11

### Fixed

- Handle changes to the [Tibber integration data structure](https://github.com/home-assistant/core/pull/160903) introduced in version 2026.2, causing entries configured to use the [Tibber integration as data source](README.md#data-source) becoming unavailable.

## [0.7.2] - 2026-01-09

### Added

- 💹 Added a new value to the [**Show min/max per day** option](docs/OPTIONS.md#show-minmax-per-day) (`on_from_today`).

### Fixed

- Handle changes to the [Tibber integration data structure](https://github.com/home-assistant/core/pull/156690) introduced in version 2026.1, causing entries configured to use the [Tibber integration as data source](README.md#data-source) becoming unavailable.

## [0.7.1] - 2025-12-05

### Added

- Added new values to the [**Show current price** option](docs/OPTIONS.md#show-current-price) (`on_in_graph_no_time`/`on_in_graph_only_marker`) and the [**Show min price**](docs/OPTIONS.md#show-min-price)/[**Show max price**](docs/OPTIONS.md#show-max-price) options (`on_no_time`/`on_only_marker`).

### Changed

- Made the cheap price highlighting a bit more discrete and less visually intrusive. Now also distinguishes between cheap price points and cheap price threshold highlights.
- Improved how the price line is colored when using the [**Color price line by average** option](docs/OPTIONS.md#color-price-line-by-average).
- Graphs are now automatically rendered when using [actions such as `set_option`, `reset_option`, `set_data_source`, `set_custom_theme`, or `create_graph`](README.md#actions).

### Fixed

- Added back missing `reconfigure_successful` string.

## [0.7.0] - 2025-11-28

### Added

- 🔃 New [**_Sensor_ refresh mode** option](docs/OPTIONS.md#refresh-mode), to update the graph image whenever the price sensor data source updates.
- 🖌️ New [**Show min/max per day** option](docs/OPTIONS.md#show-minmax-per-day) to display minimum and maximum price labels for each day separately.
- 🖌️ New [**Show data source name** option](docs/OPTIONS.md#show-data-source-name) to display the data source friendly name in the graph footer.
- 🎬 New [`export_config` action](README.md#tibber_graphexport_config) to export the current configuration for a Tibber Graph entity, making it easy to recreate entities or share configurations.

### Changed

- **Default behavior**: By default the graph now shows minimum and maximum price labels for each day separately when enabled. To restore the previous default behavior, disable the new **Show min/max per day** option.
- Simplified options UI by removing some of the more exotic options (unlikely to be used by most users). These options can still be set using the [`create_graph`](README.md#tibber_graphcreate_graph) or [`set_option`](README.md#tibber_graphset_option) actions, see notes in [OPTIONS.md](docs/OPTIONS.md).

## [0.6.2] - 2025-11-23

### Added

- 🖌️ **Cheap boundary highlight**: New [`cheap_boundary_highlight` option](docs/OPTIONS.md#cheap-boundary-highlight) to highlight start and end time labels of cheap periods for greater visibility.
- **Show cheap price line**: New [`show_cheap_price_line` option](docs/OPTIONS.md#show-cheap-price-line) to draw a horizontal line at the provided cheap price threshold.
- 🎨 **New theme properties** (see [CUSTOM_THEME.md](docs/CUSTOM_THEME.md#theme-properties) for details):
  - `avgline_color` and `avgline_style` for the average price line color and style.
  - `cheapline_color` and `cheapline_style` for the cheap price threshold line color and style.

### Changed

- 🎨 **Theme properties now optional**: Any property not provided as part of a custom theme will fall back to the configured built-in theme.

### Fixed

- Remove inaccurate timestamp parsing warning generated under some circumstances:

  ```log
  2025-11-21 06:00:29.793 WARNING (MainThread) [custom_components.tibber_graph.camera] Failed to parse 24 timestamp(s) for Tibber Graph ...
  ```

## [0.6.1] - 2025-11-19

### Added

- 🔀 Added support for **any** price sensor as a data source when created/updated using the [`create_graph`](README.md#tibber_graphcreate_graph) or [`set_data_source`](README.md#tibber_graphset_data_source) actions. See [Custom attributes & fields](README.md#custom-attributes--fields) for details and examples.

### Fixed

- Fixed issue with price line rendering around the now line.
- Improved how cheap periods are highlighted on the X-axis.
- Fixed issue with the [image entity](README.md#imagetibber_graph_entity_name) reloading the PNG too frequently.
- Other minor bug fixes and improvements.

## [0.6.0] - 2025-11-14

### Added

- 🖼️ **Image entity**: `image.tibber_graph_{entity_name}` exposing the rendered graph as an [image entity](https://www.home-assistant.io/integrations/image/).
- 🎬 **New actions** (see [README.md](README.md#actions) for usage examples):
  - `create_graph` to create entries programmatically with specified configuration, including options and custom themes.
  - `delete_graph` to delete entries programmatically.

### Changed

- 🔃 Changed the auto-refresh setting into a [refresh mode with more options](docs/OPTIONS.md#refresh-settings) for better control.
- 💶 Improved [how the currency is determined](docs/OPTIONS.md#currency-override) when using a custom data source.
- Simplified options UI by merging options where applicable.
- Rearranged options UI for improved usability.
- Related entities are now grouped under a device for easier management.

## [0.5.2] - 2025-11-08

### Changed

- 🕐 **Cheap period labels**: Now displayed on a separate row below the regular X-axis for better readability.

### Fixed

- Fixed an issue with rendering cheap periods on the X-axis, using the **Show cheap periods on X-axis** option, and not showing tick marks.
- Fixed `render` action when no `entity_id` is provided.

## [0.5.1] - 2025-11-07

### Added

- 🕐 **Show cheap periods on X-axis** option to display cheap period start/end times on the X-axis when highlighting cheap periods.
- 🔧 **Overwrite parameter** for `set_option` action to reset unprovided options to defaults.

### Fixed

- Last update sensor now correctly displays user-customized friendly names for custom data source entities.

## [0.5.0] - 2025-11-06

### Added

- 🎨 **Custom theme support**: Apply [custom color schemes](docs/CUSTOM_THEME.md) dynamically to any Tibber Graph entity. Custom themes persist across restarts and take precedence over the configured theme.
- 🎬 **Actions for configuration and rendering** (see [README.md](README.md#actions) for usage examples):
  - `set_option` to update any UI option.
  - `reset_option` to reset options to default values.
  - `set_data_source` to change the price data source.
  - `render` to render the graph.
  - `set_custom_theme` to dynamically set a custom color scheme.
- New **Last update sensor** (`sensor.tibber_graph_{entity_name}_last_update`) that provides the timestamp of the last successful image render for each camera entity, with attributes showing the data source entity ID and friendly name.
- New **Show additional info in header** option to display average price and percentage difference from average in the header alongside current price.
- New **Cheap price threshold** option to set a price threshold (e.g., 0.5 = 50 öre) below which periods are highlighted as cheap, working in combination with **Cheap price points**.

### Changed

- **Default behavior**: By default the graph now shows additional info (average price and percentage difference) in the header alongside current price when **Show current price in header** is enabled. To restore the previous default behavior, disable **Show additional info in header** in the options.

## [0.4.1] - 2025-11-01

### Added

- 🪟 New **Transparent background** option, replacing the previous **Dark (black background)** theme, to enable transparent background for both dark and light themes. Useful for OLED displays or custom dashboards.

### Changed

- Minor UI tweaks.

## [0.4.0] - 2025-10-31 🧛🏻

### Added

- 🔀 **Custom entity support**: Configure Tibber Graph to read price data from any Home Assistant sensor entity (instead of the Tibber integration). The entity must have either a `prices` or `data` attribute containing a list of prices with `start_time`|`start`|`startsAt` and `price`|`price_per_kwh`|`total` fields - see [README.md](README.md#custom-data-source) for examples. The price data source is selected during setup and cannot be changed after creation.

### Changed

- **Tibber integration is now optional**: If not using a custom entity, the Tibber integration must be configured before setting up Tibber Graph.

## [0.3.0] - 2025-10-30 🎃

### Added

- 🔢 **Multiple entity support**: Create multiple independent Tibber Graph camera entities, each with its own configuration
- New `entity_name` configuration option to customize the name of each entity

### Changed

- **Default behavior**: By default, the graph now displays a dotted horizontal line, the price line colors dynamically based on average price, and the current price label appears centered at the top. To restore the previous default behavior; disable **Show average price line**, **Color price line by average**, and **Show current price at top** in the options. To go back to the previous default canvas size, set **Canvas width** to `1200` and **Canvas height** to `700`.

## [0.2.1] - 2025-10-23

### Added

- 🕐 New **Hours to show** option to limit the number of hours displayed on the graph. When set, the graph shows from the start time (midnight or current hour, depending on the **Start graph at** setting) up to the specified number of hours or the last available data point, whichever comes first.

## [0.2.0] - 2025-10-20

### Changed

- 🖱️ **BREAKING**: Removed support for legacy YAML configuration. The component now requires configuration through the UI (**Settings → Devices & services → Add Integration → Tibber Graph**). Existing YAML configurations must be migrated to config flow entries.

## [0.1.0] - 2025-10-17

### Added

- 🚧 Initial implementation of Tibber Graph camera component
