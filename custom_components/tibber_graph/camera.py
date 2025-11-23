"""Camera platform for Tibber Graph component."""
from __future__ import annotations

import asyncio
import datetime
import logging
import random
from bisect import bisect_right
from pathlib import Path
from typing import Any

from homeassistant.components.local_file.camera import LocalFile
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import translation
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.start import async_at_started
from homeassistant.util import dt as dt_util

from .migration import (
    migrate_start_graph_at_option,
    migrate_dark_black_theme,
    migrate_label_current_option,
    migrate_show_x_axis_tick_marks_option,
    migrate_label_current_and_header_merge,
    migrate_label_max_and_show_price_merge,
    migrate_label_min_and_show_price_merge,
    migrate_show_y_axis_and_tick_marks_merge,
    migrate_cheap_periods_on_x_axis_merge,
    migrate_refresh_mode_option,
)
from .const import (
    DOMAIN,
    # General config keys
    CONF_ENTITY_NAME,
    CONF_PRICE_ENTITY_ID,
    # Custom data source config keys
    CONF_DATA_ATTR,
    CONF_DATA_ATTR_PRICE_FIELD,
    CONF_DATA_ATTR_START_FIELD,
    CONF_DATA_ATTR_START_FMT,
    CONF_DATA_ATTR_PRICE_FACTOR,
    CONF_DATA_ATTR_PRICE_ADD,
    CONF_CURRENCY_ATTR,
    # Supported attribute/field lists
    SUPPORTED_DATA_ATTRIBUTES,
    SUPPORTED_START_TIME_FIELDS,
    SUPPORTED_PRICE_FIELDS,
    CONF_THEME,
    CONF_CUSTOM_THEME,
    CONF_TRANSPARENT_BACKGROUND,
    CONF_CANVAS_WIDTH,
    CONF_CANVAS_HEIGHT,
    CONF_FORCE_FIXED_SIZE,
    # X-axis config keys
    CONF_SHOW_X_AXIS,
    CONF_CHEAP_PERIODS_ON_X_AXIS,
    CONF_START_GRAPH_AT,
    CONF_X_TICK_STEP_HOURS,
    CONF_HOURS_TO_SHOW,
    CONF_SHOW_VERTICAL_GRID,
    CONF_CHEAP_BOUNDARY_HIGHLIGHT,
    # Y-axis config keys
    CONF_SHOW_Y_AXIS,
    CONF_SHOW_HORIZONTAL_GRID,
    CONF_SHOW_AVERAGE_PRICE_LINE,
    CONF_SHOW_CHEAP_PRICE_LINE,
    CONF_CHEAP_PRICE_POINTS,
    CONF_CHEAP_PRICE_THRESHOLD,
    CONF_Y_AXIS_LABEL_ROTATION_DEG,
    CONF_Y_AXIS_SIDE,
    CONF_Y_TICK_COUNT,
    CONF_Y_TICK_USE_COLORS,
    # Price label config keys
    CONF_USE_HOURLY_PRICES,
    CONF_USE_CENTS,
    CONF_CURRENCY_OVERRIDE,
    CONF_LABEL_CURRENT,
    CONF_LABEL_FONT_SIZE,
    CONF_LABEL_MAX,
    CONF_LABEL_MIN,
    CONF_LABEL_SHOW_CURRENCY,
    CONF_LABEL_USE_COLORS,
    CONF_PRICE_DECIMALS,
    CONF_COLOR_PRICE_LINE_BY_AVERAGE,
    # Refresh config keys
    CONF_REFRESH_MODE,
    # Start graph at options
    START_GRAPH_AT_MIDNIGHT,
    START_GRAPH_AT_CURRENT_HOUR,
    START_GRAPH_AT_SHOW_ALL,
    # Configurable defaults
    DEFAULT_THEME,
    DEFAULT_TRANSPARENT_BACKGROUND,
    DEFAULT_CANVAS_WIDTH,
    DEFAULT_CANVAS_HEIGHT,
    DEFAULT_FORCE_FIXED_SIZE,
    DEFAULT_SHOW_X_AXIS,
    DEFAULT_CHEAP_PERIODS_ON_X_AXIS,
    DEFAULT_START_GRAPH_AT,
    DEFAULT_X_TICK_STEP_HOURS,
    DEFAULT_HOURS_TO_SHOW,
    DEFAULT_SHOW_VERTICAL_GRID,
    DEFAULT_CHEAP_BOUNDARY_HIGHLIGHT,
    DEFAULT_SHOW_Y_AXIS,
    DEFAULT_SHOW_HORIZONTAL_GRID,
    DEFAULT_SHOW_AVERAGE_PRICE_LINE,
    DEFAULT_SHOW_CHEAP_PRICE_LINE,
    DEFAULT_CHEAP_PRICE_POINTS,
    DEFAULT_CHEAP_PRICE_THRESHOLD,
    DEFAULT_Y_AXIS_LABEL_ROTATION_DEG,
    DEFAULT_Y_AXIS_SIDE,
    DEFAULT_Y_TICK_COUNT,
    DEFAULT_Y_TICK_USE_COLORS,
    DEFAULT_USE_HOURLY_PRICES,
    DEFAULT_USE_CENTS,
    DEFAULT_CURRENCY_OVERRIDE,
    DEFAULT_LABEL_CURRENT,
    DEFAULT_LABEL_FONT_SIZE,
    DEFAULT_LABEL_MAX,
    DEFAULT_LABEL_MIN,
    LABEL_MAX_ON,
    LABEL_MAX_ON_NO_PRICE,
    LABEL_MAX_OFF,
    LABEL_MIN_ON,
    LABEL_MIN_ON_NO_PRICE,
    LABEL_MIN_OFF,
    DEFAULT_LABEL_SHOW_CURRENCY,
    DEFAULT_LABEL_USE_COLORS,
    DEFAULT_PRICE_DECIMALS,
    DEFAULT_COLOR_PRICE_LINE_BY_AVERAGE,
    DEFAULT_REFRESH_MODE,
    REFRESH_MODE_SYSTEM,
    REFRESH_MODE_SYSTEM_INTERVAL,
    REFRESH_MODE_INTERVAL,
    REFRESH_MODE_MANUAL,
    # Non-configurable defaults (not exposed in options flow)
    DEFAULT_BOTTOM_MARGIN,
    DEFAULT_LEFT_MARGIN,
    DEFAULT_X_AXIS_LABEL_Y_OFFSET,
    DEFAULT_Y_AXIS_LABEL_VERTICAL_ANCHOR,
    DEFAULT_LABEL_CURRENT_IN_HEADER_FONT_WEIGHT,
    DEFAULT_LABEL_CURRENT_IN_HEADER_PADDING,
    DEFAULT_LABEL_FONT_WEIGHT,
    DEFAULT_LABEL_MAX_BELOW_POINT,
    DEFAULT_MIN_REDRAW_INTERVAL_SECONDS,
    DEFAULT_RENDER_STAGGER_MAX_SECONDS,
    DEFAULT_REFRESH_INTERVAL_DELAY_SECONDS,
)

from .renderer import render_plot_to_path
from .helpers import get_graph_file_path, get_unique_id, ensure_timezone

_LOGGER = logging.getLogger(__name__)

# Module-level lock for staggering entity renders across all instances
_RENDER_STAGGER_LOCK = asyncio.Lock()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tibber Graph camera from a config entry."""
    Path(hass.config.path("www/")).mkdir(parents=True, exist_ok=True)
    entities = []

    # Get options with fallbacks to defaults
    options = entry.options if entry.options else {}

    # Get entity name from config entry data
    entity_name = entry.data.get(CONF_ENTITY_NAME, entry.title or "Tibber Graph")

    # Get price entity ID from config entry data
    price_entity_id = entry.data.get(CONF_PRICE_ENTITY_ID)

    if price_entity_id:
        # Use entity as price source
        _LOGGER.info("Setting up Tibber Graph camera using entity: %s", price_entity_id)
        entities.append(TibberCam(None, hass, entry, options, entity_name, price_entity_id))
    else:
        # Use Tibber integration as price source
        if "tibber" not in hass.config.components or "tibber" not in hass.data:
            _LOGGER.error("Tibber integration not configured and no price entity provided")
            return

        for home in hass.data["tibber"].get_homes(only_active=True):
            if not home.info:
                await home.update_info()
            entities.append(TibberCam(home, hass, entry, options, entity_name, None))

    _LOGGER.info("Setting up %d Tibber Graph camera(s)", len(entities))
    async_add_entities(entities)


class TibberCam(LocalFile):
    """Camera entity that generates a dynamic Tibber price graph image."""

    def __init__(self, home, hass, entry: ConfigEntry | None, options: dict[str, Any], entity_name: str, price_entity_id: str | None = None):
        """Initialize the Tibber Graph camera."""
        # Always prefix entity name with "Tibber Graph"
        self._name = f"Tibber Graph {entity_name}"
        # Use helper function to generate file path
        self._path = get_graph_file_path(hass, entity_name)
        self._home = home
        self._price_entity_id = price_entity_id
        self.hass = hass
        self._entry = entry
        self._options = options
        self._last_update = dt_util.now() - datetime.timedelta(hours=1)
        self._render_lock = asyncio.Lock()
        # Use helper function to generate unique ID
        self._uniqueid = get_unique_id("camera", entity_name, entry.entry_id if entry else "default")
        self._refresh_unsub = None
        self._refresh_interval_hourly = None  # Track detected interval for sensor attribute
        self._cached_use_hourly_prices = None  # Cache hourly pricing detection result

        # Cache data source attribute configuration (determined once at init/update)
        self._cached_data_attr = None
        self._cached_start_field = None
        self._cached_price_field = None
        self._cached_currency_attr = None
        self._cached_start_fmt = None
        self._cached_price_factor = None
        self._cached_price_add = None
        # Initialize cached attributes
        self._determine_data_source_config()

        # Set up device info to group camera and sensor together
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}")},
            name=f"Tibber Graph {entity_name}",
            manufacturer="stefanes",
            model="Tibber Graph",
            entry_type=None,
        )

        super().__init__(self._name, self._path, self._uniqueid)

        # Run migrations for deprecated configuration options
        # Note: After migration, cached values should be invalidated
        self._options = migrate_start_graph_at_option(self.hass, self._entry, self._options, self._name)
        self._options = migrate_dark_black_theme(self.hass, self._entry, self._options, self._name)
        self._options = migrate_label_current_option(self.hass, self._entry, self._options, self._name)
        self._options = migrate_show_x_axis_tick_marks_option(self.hass, self._entry, self._options, self._name)
        self._options = migrate_label_current_and_header_merge(self.hass, self._entry, self._options, self._name)
        self._options = migrate_label_max_and_show_price_merge(self.hass, self._entry, self._options, self._name)
        self._options = migrate_label_min_and_show_price_merge(self.hass, self._entry, self._options, self._name)
        self._options = migrate_show_y_axis_and_tick_marks_merge(self.hass, self._entry, self._options, self._name)
        self._options = migrate_cheap_periods_on_x_axis_merge(self.hass, self._entry, self._options, self._name)
        self._options = migrate_refresh_mode_option(self.hass, self._entry, self._options, self._name)

    def _get_option(self, key: str, fallback: Any) -> Any:
        """Get an option value with fallback to defaults."""
        # Priority: UI options > initial data (from setup) > defaults.py
        if self._options and key in self._options:
            value = self._options[key]
            # Handle empty string for currency override
            if key == CONF_CURRENCY_OVERRIDE and value == "":
                return None
            return value
        # Check entry.data for initial configuration (e.g., theme during setup)
        if self._entry and key in self._entry.data:
            value = self._entry.data[key]
            if key == CONF_CURRENCY_OVERRIDE and value == "":
                return None
            return value
        return fallback

    def _determine_data_source_config(self) -> None:
        """Determine and cache data source attribute configuration.

        This method should be called once when the entity is created or when
        the data source is updated. It determines which attributes to use for
        custom data sources and caches them for efficient access during rendering.
        """
        if not self._price_entity_id:
            # Using Tibber integration - no custom attributes needed
            return

        # Get configured or default attribute names
        self._cached_data_attr = self._get_data_source_config(CONF_DATA_ATTR) or SUPPORTED_DATA_ATTRIBUTES[0]
        self._cached_start_field = self._get_data_source_config(CONF_DATA_ATTR_START_FIELD) or SUPPORTED_START_TIME_FIELDS[0]
        self._cached_price_field = self._get_data_source_config(CONF_DATA_ATTR_PRICE_FIELD) or SUPPORTED_PRICE_FIELDS[0]

        # Get optional attributes (can be None)
        self._cached_currency_attr = self._get_data_source_config(CONF_CURRENCY_ATTR)
        self._cached_start_fmt = self._get_data_source_config(CONF_DATA_ATTR_START_FMT)
        self._cached_price_factor = self._get_data_source_config(CONF_DATA_ATTR_PRICE_FACTOR)
        self._cached_price_add = self._get_data_source_config(CONF_DATA_ATTR_PRICE_ADD)

    def _get_data_source_config(self, key: str) -> Any:
        """Get a custom data source configuration value from entry data.

        Returns the configured value or None if not set (which means use defaults).
        Only reads from entry.data, not from options.
        """
        if self._entry and key in self._entry.data:
            return self._entry.data[key]
        return None

    def _apply_price_transformations(self, price: float) -> float:
        """Apply configured transformations to a price value.

        Args:
            price: The raw price value

        Returns:
            The transformed price value
        """
        # Apply multiplication factor (e.g., MWh to kWh conversion or VAT)
        if self._cached_price_factor is not None and self._cached_price_factor != 0:
            price = price * self._cached_price_factor

        # Add fixed amount
        if self._cached_price_add is not None:
            price = price + self._cached_price_add

        return price

    @staticmethod
    def _get_field_value(item: dict, primary_field: str, fallback_fields: list[str]):
        """Get value from dict, trying primary field first, then fallbacks.

        Args:
            item: Dictionary to search in
            primary_field: The preferred field name
            fallback_fields: List of fallback field names to try

        Returns:
            The field value or None if not found
        """
        # Try primary field first
        value = item.get(primary_field)
        if value is not None:
            return value

        # Try fallback fields
        for field in fallback_fields:
            if field != primary_field:
                value = item.get(field)
                if value is not None:
                    return value

        return None

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass - start interval refresh if enabled."""
        await super().async_added_to_hass()

        # Check refresh mode for startup handling
        refresh_mode = self._get_option(CONF_REFRESH_MODE, DEFAULT_REFRESH_MODE)

        # For system and system_interval modes, trigger initial render on Home Assistant startup
        if refresh_mode in [REFRESH_MODE_SYSTEM, REFRESH_MODE_SYSTEM_INTERVAL]:
            async_at_started(self.hass, self._async_startup_render)
            _LOGGER.debug("Registered startup render for %s with mode %s", self._name, refresh_mode)

        # Start interval refresh if enabled (uses Home Assistant's event system instead of blocking tasks)
        if refresh_mode in [REFRESH_MODE_SYSTEM_INTERVAL, REFRESH_MODE_INTERVAL]:
            # Schedule next refresh based on pricing interval
            await self._schedule_next_refresh()
            _LOGGER.debug("Started interval refresh for %s with mode %s", self._name, refresh_mode)

    async def async_will_remove_from_hass(self):
        """Cancel the interval refresh when entity is removed or reloaded."""
        if self._refresh_unsub:
            self._refresh_unsub()
            self._refresh_unsub = None

    def _detect_hourly_pricing(self) -> bool:
        """Detect whether the pricing data is hourly or 15-minute based on source data.

        Returns:
            bool: True if hourly pricing should be used, False for 15-minute pricing
        """
        # Return cached value if available
        if self._cached_use_hourly_prices is not None:
            return self._cached_use_hourly_prices

        # First check if use_hourly_prices is explicitly enabled
        use_hourly_config = self._get_option(CONF_USE_HOURLY_PRICES, DEFAULT_USE_HOURLY_PRICES)
        if use_hourly_config:
            self._cached_use_hourly_prices = True
            return True

        # Try to detect from actual price data
        try:
            dates, _ = self._parse_price_data()
            if dates and len(dates) >= 2:
                # Check the interval between first two data points
                time_diff = (dates[1] - dates[0]).total_seconds() / 60  # in minutes
                # If interval is less than 60 minutes, it's quarterly (15-minute) data
                # Otherwise it's hourly data
                result = time_diff >= 60
                self._cached_use_hourly_prices = result
                _LOGGER.debug(
                    "Detected %s pricing data for %s (interval: %.1f minutes)",
                    "hourly" if result else "15-minute", self._name, time_diff
                )
                return result
        except Exception as err:
            _LOGGER.debug(
                "Could not detect pricing interval for %s, defaulting based on configuration: %s",
                self._name, err
            )

        # Fallback to configuration and cache it
        self._cached_use_hourly_prices = use_hourly_config
        return use_hourly_config

    async def _schedule_next_refresh(self) -> None:
        """Schedule the next interval refresh based on pricing interval.

        Refreshes at a configurable delay after each pricing interval boundary:
        - For 15-minute pricing: delay after every 15-minute interval (e.g., with 30s delay: 00:00:30, 00:15:30, 00:30:30, 00:45:30)
        - For hourly pricing: delay after every hour (e.g., with 30s delay: 00:00:30, 01:00:30, 02:00:30)
        """
        # Cancel existing timer if any
        if self._refresh_unsub:
            self._refresh_unsub()
            self._refresh_unsub = None

        # Determine pricing interval from source data or configuration
        use_hourly = self._detect_hourly_pricing()
        self._refresh_interval_hourly = use_hourly  # Store for sensor attribute

        # Get the delay in seconds from configuration
        delay_seconds = DEFAULT_REFRESH_INTERVAL_DELAY_SECONDS

        now = dt_util.now()
        now_local = dt_util.as_local(now)

        # Convert current time to total seconds since midnight for easier calculation
        current_seconds = now_local.hour * 3600 + now_local.minute * 60 + now_local.second

        if use_hourly:
            # Hourly intervals: calculate next hour boundary + delay
            interval_seconds = 3600  # 1 hour
            interval_name = "hourly"
        else:
            # 15-minute intervals: calculate next 15-min boundary + delay
            interval_seconds = 900  # 15 minutes
            interval_name = "15-minute"

        # Calculate the next interval boundary + delay
        # Find how many complete intervals have passed
        intervals_passed = current_seconds // interval_seconds

        # Calculate the target time for the current interval
        current_interval_target = intervals_passed * interval_seconds + delay_seconds

        # If we've already passed this interval's target time, move to the next interval
        if current_seconds >= current_interval_target:
            next_interval_target = (intervals_passed + 1) * interval_seconds + delay_seconds
        else:
            next_interval_target = current_interval_target

        # Convert back to time
        target_seconds = next_interval_target % 86400  # Wrap around at midnight
        target_hour = target_seconds // 3600
        target_minute = (target_seconds % 3600) // 60
        target_second = target_seconds % 60

        # Create the next refresh time
        next_refresh = now_local.replace(hour=target_hour, minute=target_minute, second=target_second, microsecond=0)

        # If we wrapped around past midnight, add a day
        if next_interval_target >= 86400:
            next_refresh = next_refresh + datetime.timedelta(days=1)

        # Ensure next_refresh is always in the future (handle edge cases)
        while next_refresh <= now_local:
            if use_hourly:
                next_refresh = next_refresh + datetime.timedelta(hours=1)
            else:
                next_refresh = next_refresh + datetime.timedelta(minutes=15)

        # Calculate the delay until next refresh
        delay = (next_refresh - now_local).total_seconds()

        _LOGGER.debug(
            "Scheduling next auto-refresh for %s at %s (%s intervals, delay: %.1f seconds)",
            self._name,
            next_refresh.strftime("%H:%M:%S"),
            interval_name,
            delay
        )

        # Schedule the callback using async_call_later
        from homeassistant.helpers.event import async_call_later
        self._refresh_unsub = async_call_later(
            self.hass,
            delay,
            self._async_auto_refresh_callback
        )

    async def _async_startup_render(self, hass: HomeAssistant) -> None:
        """Callback triggered when Home Assistant has started.

        This provides an initial graph render on startup for system and system_interval modes.
        """
        try:
            _LOGGER.debug("Home Assistant startup render triggered for %s", self._name)
            await self.async_render_image(width=None, height=None, force_render=True, triggered_by="home_assistant_startup")
        except Exception as err:
            _LOGGER.error("Failed to render on Home Assistant startup for %s: %s", self._name, err, exc_info=True)

    async def _async_auto_refresh_callback(self, now: datetime.datetime) -> None:
        """Callback triggered by Home Assistant's event system for periodic interval refresh.

        This is called at the scheduled time and does not block Home Assistant startup
        or other integrations. After rendering, it schedules the next refresh.
        """
        try:
            _LOGGER.debug("Interval refresh triggered for %s", self._name)
            await self.async_render_image(width=None, height=None, force_render=False, triggered_by="interval_refresh")

            # Schedule the next refresh after completing this one
            await self._schedule_next_refresh()
        except Exception as err:
            _LOGGER.error("Failed to interval refresh %s: %s", self._name, err, exc_info=True)
            # Try to reschedule even if this refresh failed
            try:
                await self._schedule_next_refresh()
            except Exception as schedule_err:
                _LOGGER.error("Failed to reschedule interval refresh for %s: %s", self._name, schedule_err)

    async def async_camera_image(self, width=None, height=None):
        """Render the graph if needed and return its bytes.

        Respects refresh_mode setting:
        - system/system_interval: Updates on camera refresh
        - interval: Only updates on interval, not on camera refresh
        - manual: Only updates on explicit actions
        """
        # Check refresh mode to determine if we should update on camera access
        refresh_mode = self._get_option(CONF_REFRESH_MODE, DEFAULT_REFRESH_MODE)

        # For 'interval' and 'manual' modes, don't trigger render on camera access
        # For 'system' and 'system_interval' modes, allow render on camera access
        should_render = refresh_mode in [REFRESH_MODE_SYSTEM, REFRESH_MODE_SYSTEM_INTERVAL]

        if should_render:
            await self.async_render_image(width=width, height=height, force_render=False, triggered_by="camera_access")

        return await self.hass.async_add_executor_job(self.camera_image)

    async def async_render_image(self, width=None, height=None, force_render=True, triggered_by="unknown"):
        """Render the graph.

        Args:
            width: Optional width override for the image
            height: Optional height override for the image
            force_render: If True, bypasses throttling to force immediate render
            triggered_by: Source that triggered the render (action, camera_access, interval_refresh, unknown)
        """
        force_fixed = self._get_option(CONF_FORCE_FIXED_SIZE, DEFAULT_FORCE_FIXED_SIZE)
        canvas_width = self._get_option(CONF_CANVAS_WIDTH, DEFAULT_CANVAS_WIDTH)
        canvas_height = self._get_option(CONF_CANVAS_HEIGHT, DEFAULT_CANVAS_HEIGHT)

        if force_fixed:
            w, h = canvas_width, canvas_height
        else:
            w = width or canvas_width
            h = height or canvas_height

        # Temporarily reset last_update to force a render if requested
        if force_render:
            old_last_update = self._last_update
            self._last_update = dt_util.now() - datetime.timedelta(hours=1)
            try:
                await self._generate_fig(w, h, triggered_by=triggered_by)
                _LOGGER.info("Manually rendered graph for %s", self._name)
            finally:
                self._last_update = old_last_update
        else:
            await self._generate_fig(w, h, triggered_by=triggered_by)

    def _parse_price_data(self):
        """Extract and filter price data for the configured range."""
        # Check if using entity or Tibber integration
        if self._price_entity_id:
            return self._parse_price_data_from_entity()
        else:
            return self._parse_price_data_from_tibber()

    def _get_date_range_filter(self):
        """Calculate the date range for filtering based on start_graph_at option.

        Returns:
            tuple: (start_date, end_date) where both are None if showing all data,
                   otherwise date objects for today and tomorrow.
        """
        start_graph_at = self._get_option(CONF_START_GRAPH_AT, DEFAULT_START_GRAPH_AT)
        if start_graph_at == START_GRAPH_AT_SHOW_ALL:
            return None, None

        now_local = dt_util.as_local(dt_util.now())
        start_date = now_local.date()
        end_date = start_date + datetime.timedelta(days=1)
        return start_date, end_date

    def _filter_and_parse_prices(self, paired, source_name):
        """Filter, sort, and optionally aggregate price data.

        Args:
            paired: List of (datetime, price) tuples
            source_name: Name of the data source for logging

        Returns:
            tuple: (dates, prices) lists, or ([], []) if no valid data
        """
        if not paired:
            _LOGGER.warning("No valid price data in date range from %s for %s",
                          source_name, self._name)
            return [], []

        # Sort once
        paired.sort(key=lambda x: x[0])
        dates, prices = zip(*paired)
        dates, prices = list(dates), list(prices)

        # Aggregate to hourly prices if configured
        use_hourly = self._get_option(CONF_USE_HOURLY_PRICES, DEFAULT_USE_HOURLY_PRICES)
        if use_hourly:
            dates, prices = self._aggregate_to_hourly(dates, prices)

        _LOGGER.debug("Parsed %d price data points from %s for %s",
                     len(prices), source_name, self._name)
        return dates, prices

    def _parse_datetime_and_price(self, timestamp_str, price_val, start_date, end_date):
        """Parse timestamp and price, applying optional date filtering.

        Args:
            timestamp_str: Timestamp string in ISO format or custom format (if data_attr_start_fmt is configured)
            price_val: Price value (will be converted to float)
            start_date: Start date for filtering (None to disable)
            end_date: End date for filtering (None to disable)

        Returns:
            tuple: (status, result) where status is one of:
                   'success': result is (datetime, price)
                   'filtered': timestamp was valid but filtered out by date range
                   'parse_error': failed to parse timestamp or price
        """
        if self._cached_start_fmt:
            # Use cached custom format string
            try:
                dt_parsed = datetime.datetime.strptime(timestamp_str, self._cached_start_fmt)
            except (ValueError, TypeError):
                # Don't log here - let the caller log once for all failures
                return ('parse_error', None)
        else:
            # Try ISO format parsing
            dt_parsed = dt_util.parse_datetime(timestamp_str)
            if not dt_parsed:
                # Don't log here - let the caller log once for all failures
                return ('parse_error', None)

        # If no timezone info, assume local time
        dt_loc = ensure_timezone(dt_parsed, dt_util.DEFAULT_TIME_ZONE)
        if dt_parsed.tzinfo is not None:
            dt_loc = dt_util.as_local(dt_parsed)

        if not dt_loc:
            return ('parse_error', None)

        # Apply date filter only if date range is configured
        if start_date is not None and end_date is not None:
            if not (start_date <= dt_loc.date() <= end_date):
                return ('filtered', None)

        try:
            price = float(price_val)
            return ('success', (dt_loc, price))
        except (TypeError, ValueError):
            return ('parse_error', None)

    def _parse_price_data_from_entity(self):
        """Extract and filter price data from a Home Assistant entity."""
        state = self.hass.states.get(self._price_entity_id)
        if not state:
            _LOGGER.warning("Price entity %s not found for %s", self._price_entity_id, self._name)
            return [], []

        # Try cached attribute first, then fall back to other supported attributes
        data = self._get_field_value(state.attributes, self._cached_data_attr, SUPPORTED_DATA_ATTRIBUTES)

        if not data:
            _LOGGER.warning("No price data in entity %s for %s (tried attributes: %s)",
                          self._price_entity_id, self._name, ", ".join(SUPPORTED_DATA_ATTRIBUTES))
            return [], []

        if not isinstance(data, list):
            _LOGGER.warning("Invalid price data format in entity %s for %s: expected list, got %s",
                          self._price_entity_id, self._name, type(data))
            return [], []

        # Get date range filter
        start_date, end_date = self._get_date_range_filter()

        # Parse price data from entity using cached field names
        paired = []
        parse_failures = 0
        first_failed_timestamp = None

        for item in data:
            if not isinstance(item, dict):
                continue

            # Get start time and price using cached field names
            time_key = self._get_field_value(item, self._cached_start_field, SUPPORTED_START_TIME_FIELDS)
            price_val = self._get_field_value(item, self._cached_price_field, SUPPORTED_PRICE_FIELDS)

            if not time_key or price_val is None:
                continue

            # Apply configured price transformations
            price_val = self._apply_price_transformations(price_val)

            status, result = self._parse_datetime_and_price(time_key, price_val, start_date, end_date)
            if status == 'success':
                paired.append(result)
            elif status == 'parse_error' and time_key:
                # Track parse failures (not filtered timestamps)
                parse_failures += 1
                if first_failed_timestamp is None:
                    first_failed_timestamp = time_key
            # status == 'filtered' is silently ignored as it's expected behavior

        # Log warning once if there were parse failures
        if parse_failures > 0 and first_failed_timestamp:
            if self._cached_start_fmt:
                _LOGGER.warning(
                    "Failed to parse %d timestamp(s) for %s with custom format '%s' (example timestamp: '%s'). "
                    "Please verify the format string matches your timestamp format. "
                    "See here for details: https://github.com/stefanes/tibber-graph/blob/main/README.md#custom-attributes--fields",
                    parse_failures, self._name, self._cached_start_fmt, first_failed_timestamp
                )
            else:
                _LOGGER.warning(
                    "Failed to parse %d timestamp(s) for %s (example timestamp: '%s'). "
                    "If your timestamps are not in ISO 8601 format, please specify 'data_attr_start_fmt' "
                    "with the appropriate format string (e.g., '%%m/%%d/%%Y %%H:%%M:%%S' for '11/17/2025 18:00:00'). "
                    "See here for details: https://github.com/stefanes/tibber-graph/blob/main/README.md#custom-attributes--fields",
                    parse_failures, self._name, first_failed_timestamp
                )

        return self._filter_and_parse_prices(paired, f"entity {self._price_entity_id}")

    def _parse_price_data_from_tibber(self):
        """Extract and filter price data from Tibber integration."""
        if not self._home:
            _LOGGER.error("Tibber home not configured for %s", self._name)
            return [], []

        data = getattr(self._home, "price_total", None)
        if not data:
            _LOGGER.warning("No price data available for %s", self._name)
            return [], []

        # Normalize data format once
        if isinstance(data, dict):
            items = data.items()
        elif isinstance(data, list):
            items = [(i.get("startsAt"), i.get("total")) for i in data]
        else:
            _LOGGER.warning("Invalid price data format for %s: %s", self._name, type(data))
            return [], []

        # Get date range filter
        start_date, end_date = self._get_date_range_filter()

        # Build price pairs using helper method
        paired = []
        parse_failures = 0
        first_failed_timestamp = None

        for k, v in items:
            status, result = self._parse_datetime_and_price(k, v, start_date, end_date)
            if status == 'success':
                paired.append(result)
            elif status == 'parse_error' and k:
                # Track parse failures (not filtered timestamps)
                parse_failures += 1
                if first_failed_timestamp is None:
                    first_failed_timestamp = k
            # status == 'filtered' is silently ignored as it's expected behavior

        # Log warning once if there were parse failures
        if parse_failures > 0 and first_failed_timestamp:
            if self._cached_start_fmt:
                _LOGGER.warning(
                    "Failed to parse %d timestamp(s) for %s with custom format '%s' (example timestamp: '%s'). "
                    "Please verify the format string matches your timestamp format. "
                    "See here for details: https://github.com/stefanes/tibber-graph/blob/main/README.md#custom-attributes--fields",
                    parse_failures, self._name, self._cached_start_fmt, first_failed_timestamp
                )
            else:
                _LOGGER.warning(
                    "Failed to parse %d timestamp(s) for %s (example timestamp: '%s'). "
                    "If your timestamps are not in ISO 8601 format, please specify 'data_attr_start_fmt' "
                    "with the appropriate format string (e.g., '%%m/%%d/%%Y %%H:%%M:%%S' for '11/17/2025 18:00:00'). "
                    "See here for details: https://github.com/stefanes/tibber-graph/blob/main/README.md#custom-attributes--fields",
                    parse_failures, self._name, first_failed_timestamp
                )

        return self._filter_and_parse_prices(paired, "Tibber integration")

    @staticmethod
    def _aggregate_to_hourly(dates, prices):
        """Aggregate 15-minute price intervals into hourly averages.

        Groups prices by hour and calculates the average of all intervals
        within each hour (typically 4 intervals of 15 minutes each).
        """
        if not dates or not prices:
            return [], []

        # Group prices by hour using defaultdict for efficiency
        from collections import defaultdict
        hourly_data = defaultdict(list)
        for date, price in zip(dates, prices):
            # Get the hour start (top of the hour)
            hour_start = date.replace(minute=0, second=0, microsecond=0)
            hourly_data[hour_start].append(price)

        # Calculate averages and sort by time in one comprehension
        sorted_hours = sorted(hourly_data.keys())
        hourly_prices = [sum(hourly_data[h]) / len(hourly_data[h]) for h in sorted_hours]

        return sorted_hours, hourly_prices

    def _get_currency_with_source(self) -> tuple[str, str]:
        """Determine the currency symbol and its source.

        Returns:
            tuple: (currency_symbol, currency_source) where currency_source is one of:
                   'currency_override', 'tibber_integration', 'currency_attribute',
                   'unit_of_measurement', or 'default'
        """
        use_cents = self._get_option(CONF_USE_CENTS, DEFAULT_USE_CENTS)
        currency_override = self._get_option(CONF_CURRENCY_OVERRIDE, DEFAULT_CURRENCY_OVERRIDE)

        # Handle use_cents mode
        if use_cents:
            # If use_cents is true and currency_override is set, use the override
            if currency_override:
                return (currency_override, "currency_override")
            # Otherwise use the cent symbol
            return ("¢", "default")

        # use_cents is false - use standard currency determination logic
        # 1. Check if user has set currency_override
        if currency_override:
            return (currency_override, "currency_override")

        # 2. If data source is Tibber integration, use Tibber's currency
        if self._home:
            currency = getattr(self._home, "currency", None)
            if currency:
                return (currency, "tibber_integration")

        # 3. If data source is custom sensor, check attributes
        if self._price_entity_id:
            state = self.hass.states.get(self._price_entity_id)
            if state:
                # 3a. Check for cached currency attribute name
                if self._cached_currency_attr:
                    # Use configured currency attribute
                    currency_attr = state.attributes.get(self._cached_currency_attr)
                    if currency_attr:
                        return (str(currency_attr), "currency_attribute")
                else:
                    # Use default 'currency' attribute as fallback
                    currency_attr = state.attributes.get("currency")
                    if currency_attr:
                        return (str(currency_attr), "currency_attribute")

                # 3b. Check for 'unit_of_measurement' attribute as fallback
                unit_of_measurement = state.attributes.get("unit_of_measurement")
                if unit_of_measurement:
                    # Extract currency symbol from unit_of_measurement
                    # Handle cases like "€/kWh", "SEK/kWh", "$/kWh", etc.
                    unit_str = str(unit_of_measurement)
                    # Split by common separators and take the first part
                    if "/" in unit_str:
                        currency = unit_str.split("/")[0].strip()
                    else:
                        currency = unit_str.strip()
                    if currency:
                        return (currency, "unit_of_measurement")

        # 4. Default to € if no currency could be determined
        return ("€", "default")

    async def _generate_fig(self, width, height, triggered_by="unknown"):
        """Throttle and trigger figure rendering in background.

        Args:
            width: Canvas width for rendering
            height: Canvas height for rendering
            triggered_by: Source that triggered the render
        """
        # Stagger renders across entities to prevent simultaneous updates
        # This uses a module-level lock with random delay to distribute load
        if DEFAULT_RENDER_STAGGER_MAX_SECONDS > 0:
            async with _RENDER_STAGGER_LOCK:
                # Add random delay to stagger entity updates
                await asyncio.sleep(random.uniform(0, DEFAULT_RENDER_STAGGER_MAX_SECONDS))

        async with self._render_lock:
            now = dt_util.now()
            if (now - self._last_update).total_seconds() < DEFAULT_MIN_REDRAW_INTERVAL_SECONDS:
                return

            # Only update Tibber data if using Tibber integration
            if self._home:
                try:
                    if self._home.last_data_timestamp is None or (self._home.last_data_timestamp - now).total_seconds() > 11 * 3600:
                        _LOGGER.debug("Fetching updated price data for %s", self._name)
                        await self._home.update_info_and_price_info()
                except Exception as err:
                    _LOGGER.warning("Failed to update Tibber data for %s: %s", self._name, err)

            self._last_update = now

            dates, prices = self._parse_price_data()
            if len(prices) < 2:
                _LOGGER.warning("Insufficient price data (%d points) to render graph for %s", len(prices), self._name)
                return

            # Determine step size based on actual data interval
            use_hourly = self._get_option(CONF_USE_HOURLY_PRICES, DEFAULT_USE_HOURLY_PRICES)
            step_minutes = int((dates[1] - dates[0]).total_seconds() // 60) or (60 if use_hourly else 15)
            interval_td = datetime.timedelta(minutes=step_minutes)
            dates_plot = list(dates) + [dates[-1] + interval_td]
            prices_plot = list(prices) + [prices[-1]]

            now_local = dt_util.as_local(dt_util.now())
            idx = bisect_right(dates, now_local) - 1
            idx = max(0, min(idx, len(prices) - 1))

            # Determine currency to display using the new helper method
            currency, currency_source = self._get_currency_with_source()

            # Collect rendering options to pass to renderer
            render_options = self._get_render_options()

            # Fetch translations for renderer labels
            translations = await self._get_translations()

            await self.hass.async_add_executor_job(
                render_plot_to_path,
                width,
                height,
                dates_plot,
                prices_plot,
                dates,
                prices,
                now_local,
                idx,
                currency,
                self._path,
                render_options,
                translations,
            )
            _LOGGER.debug("Rendered graph for %s (triggered by: %s)", self._name, triggered_by)

            # Fire event for sensor updates
            self.hass.bus.async_fire(
                "tibber_graph_updated",
                {
                    "entity_id": self.entity_id,
                    "timestamp": self._last_update,
                    "triggered_by": triggered_by,
                },
            )

    async def _get_translations(self) -> dict[str, str]:
        """Fetch translated strings for renderer labels.

        Returns a dictionary with translated strings for use in the rendered image.
        Falls back to English if translations are not available.
        """
        try:
            # Get the current user's language, or fall back to the system language
            translations_dict = await translation.async_get_translations(
                self.hass,
                self.hass.config.language,
                "renderer",
                {DOMAIN},
            )

            # Extract labels from translations
            # The key format is: "component.{domain}.entity.camera.{platform}.state_attributes.{key}.name"
            label_at_key = f"component.{DOMAIN}.entity.camera.tibber_graph.state_attributes.label_at.name"
            label_at = translations_dict.get(label_at_key, "at")
            label_avg_key = f"component.{DOMAIN}.entity.camera.tibber_graph.state_attributes.label_avg.name"
            label_avg = translations_dict.get(label_avg_key, "avg.")

            return {
                "label_at": label_at,
                "label_avg": label_avg,
            }
        except Exception as err:
            _LOGGER.debug("Failed to fetch translations for %s: %s. Using fallback.", self._name, err)
            # Fallback to English
            return {
                "label_at": "at",
                "label_avg": "avg.",
            }

    def _get_render_options(self) -> dict[str, Any]:
        """Collect rendering options from config entry (UI) or defaults.py."""
        return {
            # General settings
            "theme": self._get_option(CONF_THEME, DEFAULT_THEME),
            "custom_theme": self._get_option(CONF_CUSTOM_THEME, None),
            "transparent_background": self._get_option(CONF_TRANSPARENT_BACKGROUND, DEFAULT_TRANSPARENT_BACKGROUND),
            "canvas_width": self._get_option(CONF_CANVAS_WIDTH, DEFAULT_CANVAS_WIDTH),
            "canvas_height": self._get_option(CONF_CANVAS_HEIGHT, DEFAULT_CANVAS_HEIGHT),
            "force_fixed_size": self._get_option(CONF_FORCE_FIXED_SIZE, DEFAULT_FORCE_FIXED_SIZE),
            "bottom_margin": DEFAULT_BOTTOM_MARGIN,
            "left_margin": DEFAULT_LEFT_MARGIN,
            # X-axis settings
            "show_x_axis": self._get_option(CONF_SHOW_X_AXIS, DEFAULT_SHOW_X_AXIS),
            "cheap_periods_on_x_axis": self._get_option(CONF_CHEAP_PERIODS_ON_X_AXIS, DEFAULT_CHEAP_PERIODS_ON_X_AXIS),
            "start_graph_at": self._get_option(CONF_START_GRAPH_AT, DEFAULT_START_GRAPH_AT),
            "x_axis_label_y_offset": DEFAULT_X_AXIS_LABEL_Y_OFFSET,
            "x_tick_step_hours": self._get_option(CONF_X_TICK_STEP_HOURS, DEFAULT_X_TICK_STEP_HOURS),
            "hours_to_show": self._get_option(CONF_HOURS_TO_SHOW, DEFAULT_HOURS_TO_SHOW),
            "show_vertical_grid": self._get_option(CONF_SHOW_VERTICAL_GRID, DEFAULT_SHOW_VERTICAL_GRID),
            "cheap_boundary_highlight": self._get_option(CONF_CHEAP_BOUNDARY_HIGHLIGHT, DEFAULT_CHEAP_BOUNDARY_HIGHLIGHT),
            # Y-axis settings
            "show_y_axis": self._get_option(CONF_SHOW_Y_AXIS, DEFAULT_SHOW_Y_AXIS),
            "show_horizontal_grid": self._get_option(CONF_SHOW_HORIZONTAL_GRID, DEFAULT_SHOW_HORIZONTAL_GRID),
            "show_average_price_line": self._get_option(CONF_SHOW_AVERAGE_PRICE_LINE, DEFAULT_SHOW_AVERAGE_PRICE_LINE),
            "show_cheap_price_line": self._get_option(CONF_SHOW_CHEAP_PRICE_LINE, DEFAULT_SHOW_CHEAP_PRICE_LINE),
            "cheap_price_points": self._get_option(CONF_CHEAP_PRICE_POINTS, DEFAULT_CHEAP_PRICE_POINTS),
            "cheap_price_threshold": self._get_option(CONF_CHEAP_PRICE_THRESHOLD, DEFAULT_CHEAP_PRICE_THRESHOLD),
            "y_axis_label_rotation_deg": self._get_option(CONF_Y_AXIS_LABEL_ROTATION_DEG, DEFAULT_Y_AXIS_LABEL_ROTATION_DEG),
            "y_axis_label_vertical_anchor": DEFAULT_Y_AXIS_LABEL_VERTICAL_ANCHOR,
            "y_axis_side": self._get_option(CONF_Y_AXIS_SIDE, DEFAULT_Y_AXIS_SIDE),
            "y_tick_count": self._get_option(CONF_Y_TICK_COUNT, DEFAULT_Y_TICK_COUNT),
            "y_tick_use_colors": self._get_option(CONF_Y_TICK_USE_COLORS, DEFAULT_Y_TICK_USE_COLORS),
            # Price label settings
            "use_hourly_prices": self._get_option(CONF_USE_HOURLY_PRICES, DEFAULT_USE_HOURLY_PRICES),
            "use_cents": self._get_option(CONF_USE_CENTS, DEFAULT_USE_CENTS),
            "currency_override": self._get_option(CONF_CURRENCY_OVERRIDE, DEFAULT_CURRENCY_OVERRIDE),
            "label_current": self._get_option(CONF_LABEL_CURRENT, DEFAULT_LABEL_CURRENT),
            "label_current_in_header_font_weight": DEFAULT_LABEL_CURRENT_IN_HEADER_FONT_WEIGHT,
            "label_current_in_header_padding": DEFAULT_LABEL_CURRENT_IN_HEADER_PADDING,
            "label_font_size": self._get_option(CONF_LABEL_FONT_SIZE, DEFAULT_LABEL_FONT_SIZE),
            "label_font_weight": DEFAULT_LABEL_FONT_WEIGHT,
            "label_max": self._get_option(CONF_LABEL_MAX, DEFAULT_LABEL_MAX),
            "label_max_below_point": DEFAULT_LABEL_MAX_BELOW_POINT,
            "label_min": self._get_option(CONF_LABEL_MIN, DEFAULT_LABEL_MIN),
            "label_show_currency": self._get_option(CONF_LABEL_SHOW_CURRENCY, DEFAULT_LABEL_SHOW_CURRENCY),
            "label_use_colors": self._get_option(CONF_LABEL_USE_COLORS, DEFAULT_LABEL_USE_COLORS),
            "price_decimals": self._get_option(CONF_PRICE_DECIMALS, DEFAULT_PRICE_DECIMALS),
            "color_price_line_by_average": self._get_option(CONF_COLOR_PRICE_LINE_BY_AVERAGE, DEFAULT_COLOR_PRICE_LINE_BY_AVERAGE),
        }
