# Changelog

All notable changes to this project will be documented in this file.

## [0.2.1] - 2025-10-23

### Added

- New `hours_to_show` option to limit the number of hours displayed on the graph. When set, the graph shows from the start time (midnight or current hour, depending on the "Start at Midnight" setting) up to the specified number of hours or the last available data point, whichever comes first.

## [0.2.0] - 2025-10-20

### Changed

- **BREAKING**: Removed support for legacy YAML configuration. The component now requires configuration through the UI (Settings → Integrations → Add Integration → Tibber Graph). Existing YAML configurations must be migrated to config flow entries.

## [0.1.0] - 2025-10-17

### Added

- Initial implementation of Tibber Graph camera component
