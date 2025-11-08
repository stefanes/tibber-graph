<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

## [0.5.2] - 2025-11-08

### Changed

- 🕐 **Cheap period labels**: Now displayed on a separate row below the regular X-axis for better readability.

### Fixed

- Fixed an issue with rendering cheap periods on the X-axis, using the **Show cheap periods on X-axis** option, and not showing tick marks.
- Fixed `tibber_graph.render` action when no `entity_id` is provided.

## [0.5.1] - 2025-11-07

### Added

- 🕐 **Show cheap periods on X-axis** option to display cheap period start/end times on the X-axis when highlighting cheap periods.
- 🔧 **Overwrite parameter** for `set_option` action to reset unprovided options to defaults.

### Fixed

- Last update sensor now correctly displays user-customized friendly names for custom data source entities.

## [0.5.0] - 2025-11-06

### Added

- 🎨 **Custom theme support**: Apply custom color schemes dynamically to any Tibber Graph entity. Custom themes persist across restarts and take precedence over the configured theme, see [CUSTOM_THEME.md](docs/CUSTOM_THEME.md) for details and examples.
- 🎬 **Actions for configuration and rendering** (see [README.md](README.md#actions) for usage examples):
  - `tibber_graph.set_option` to update any UI option.
  - `tibber_graph.reset_option` to reset options to default values.
  - `tibber_graph.set_data_source` to change the price data source.
  - `tibber_graph.render` to render the graph.
  - `tibber_graph.set_custom_theme` to dynamically set a custom color scheme.
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

- 🖱️ **BREAKING**: Removed support for legacy YAML configuration. The component now requires configuration through the UI (**Settings → Integrations → Add Integration → Tibber Graph**). Existing YAML configurations must be migrated to config flow entries.

## [0.1.0] - 2025-10-17

### Added

- 🚧 Initial implementation of Tibber Graph camera component
