# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0] - 2025-10-31 🧛🏻

### Added

- **Custom entity support**: Configure Tibber Graph to read price data from any Home Assistant sensor entity (instead of the Tibber integration). The entity must have either a `prices` or `data` attribute containing a list of prices with `start_time`|`start`|`startsAt` and `price`|`price_per_kwh`|`total` fields - see [README.md](README.md) for examples. The price data source is selected during setup and cannot be changed after creation.
- **Dark (black background) theme**: New theme option with OLED-friendly pure black background.

### Changed

- Tibber integration is now optional. If not using a custom entity, the Tibber integration must be configured before setting up Tibber Graph. The component will show an error if neither a price entity nor the Tibber integration is available.

## [0.3.0] - 2025-10-30 🎃

### Added

- **Multiple entity support**: Create multiple independent Tibber Graph camera entities, each with its own configuration
- New `entity_name` configuration option to customize the name of each entity

### Changed

- **BREAKING**: Camera entity names now based on configured `entity_name` instead of Tibber home address
- PNG files now named as `tibber_graph_{entity_name}.png`
- **Default behavior**: By default, the graph now displays a dotted horizontal line, the price line colors dynamically based on average price, and the current price label appears centered at the top. To restore the previous default behavior, disable **"Show average price line"**, **"Color price line by average"**, and **"Show current price at top"** in the options. To go back to the previous default canvas size, set **Canvas width** to 1200 and **Canvas height** to 700.

## [0.2.1] - 2025-10-23

### Added

- New `hours_to_show` option to limit the number of hours displayed on the graph. When set, the graph shows from the start time (midnight or current hour, depending on the "Start at Midnight" setting) up to the specified number of hours or the last available data point, whichever comes first.

## [0.2.0] - 2025-10-20

### Changed

- **BREAKING**: Removed support for legacy YAML configuration. The component now requires configuration through the UI (Settings → Integrations → Add Integration → Tibber Graph). Existing YAML configurations must be migrated to config flow entries.

## [0.1.0] - 2025-10-17

### Added

- Initial implementation of Tibber Graph camera component
