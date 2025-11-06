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
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers import translation
from homeassistant.util import dt as dt_util

from .migration import (
    migrate_start_graph_at_option,
    migrate_dark_black_theme,
    migrate_label_current_option,
)
from .const import (
    DOMAIN,
    # General config keys
    CONF_ENTITY_NAME,
    CONF_PRICE_ENTITY_ID,
    CONF_THEME,
    CONF_CUSTOM_THEME,
    CONF_TRANSPARENT_BACKGROUND,
    CONF_CANVAS_WIDTH,
    CONF_CANVAS_HEIGHT,
    CONF_FORCE_FIXED_SIZE,
    # X-axis config keys
    CONF_SHOW_X_TICKS,
    CONF_START_GRAPH_AT,
    CONF_X_TICK_STEP_HOURS,
    CONF_HOURS_TO_SHOW,
    CONF_SHOW_VERTICAL_GRID,
    # Y-axis config keys
    CONF_SHOW_Y_AXIS,
    CONF_SHOW_Y_AXIS_TICKS,
    CONF_SHOW_HORIZONTAL_GRID,
    CONF_SHOW_AVERAGE_PRICE_LINE,
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
    CONF_LABEL_CURRENT_IN_HEADER,
    CONF_LABEL_CURRENT_IN_HEADER_MORE,
    CONF_LABEL_FONT_SIZE,
    CONF_LABEL_MAX,
    CONF_LABEL_MIN,
    CONF_LABEL_MINMAX_SHOW_PRICE,
    CONF_LABEL_SHOW_CURRENCY,
    CONF_LABEL_USE_COLORS,
    CONF_PRICE_DECIMALS,
    CONF_COLOR_PRICE_LINE_BY_AVERAGE,
    # Refresh config keys
    CONF_AUTO_REFRESH_ENABLED,
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
    DEFAULT_SHOW_X_TICKS,
    DEFAULT_START_GRAPH_AT,
    DEFAULT_X_TICK_STEP_HOURS,
    DEFAULT_HOURS_TO_SHOW,
    DEFAULT_SHOW_VERTICAL_GRID,
    DEFAULT_SHOW_Y_AXIS,
    DEFAULT_SHOW_Y_AXIS_TICKS,
    DEFAULT_SHOW_HORIZONTAL_GRID,
    DEFAULT_SHOW_AVERAGE_PRICE_LINE,
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
    DEFAULT_LABEL_CURRENT_IN_HEADER,
    DEFAULT_LABEL_CURRENT_IN_HEADER_MORE,
    DEFAULT_LABEL_FONT_SIZE,
    DEFAULT_LABEL_MAX,
    DEFAULT_LABEL_MIN,
    DEFAULT_LABEL_MINMAX_SHOW_PRICE,
    DEFAULT_LABEL_SHOW_CURRENCY,
    DEFAULT_LABEL_USE_COLORS,
    DEFAULT_PRICE_DECIMALS,
    DEFAULT_COLOR_PRICE_LINE_BY_AVERAGE,
    DEFAULT_AUTO_REFRESH_ENABLED,
    # Non-configurable defaults (not exposed in options flow)
    DEFAULT_BOTTOM_MARGIN,
    DEFAULT_LEFT_MARGIN,
    DEFAULT_X_AXIS_LABEL_Y_OFFSET,
    DEFAULT_Y_AXIS_LABEL_VERTICAL_ANCHOR,
    DEFAULT_LABEL_CURRENT_IN_HEADER_FONT_WEIGHT,
    DEFAULT_LABEL_CURRENT_IN_HEADER_PADDING,
    DEFAULT_LABEL_FONT_WEIGHT,
    DEFAULT_LABEL_MAX_BELOW_POINT,
    DEFAULT_AUTO_REFRESH_INTERVAL_MINUTES,
    DEFAULT_MIN_REDRAW_INTERVAL_SECONDS,
    DEFAULT_RENDER_STAGGER_MAX_SECONDS,
)

from .renderer import render_plot_to_path

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
        # Create a sanitized version for file paths and unique IDs
        name_sanitized = entity_name.lower().replace(" ", "_").replace("-", "_")
        # Add entry_id to ensure uniqueness in Home Assistant's unique_id system
        unique_suffix = entry.entry_id.split("-")[0] if entry else "default"
        # Filename only uses entity_name since entity names are unique per instance
        self._path = hass.config.path(f"www/tibber_graph_{name_sanitized}.png")
        self._home = home
        self._price_entity_id = price_entity_id
        self.hass = hass
        self._entry = entry
        self._options = options
        self._last_update = dt_util.now() - datetime.timedelta(hours=1)
        self._render_lock = asyncio.Lock()
        self._uniqueid = f"camera_tibber_graph_{name_sanitized}_{unique_suffix}"
        self._refresh_unsub = None
        super().__init__(self._name, self._path, self._uniqueid)

        # Run migrations for deprecated configuration options
        self._options = migrate_start_graph_at_option(self.hass, self._entry, self._options, self._name)
        self._options = migrate_dark_black_theme(self.hass, self._entry, self._options, self._name)
        self._options = migrate_label_current_option(self.hass, self._entry, self._options, self._name)

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

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass - start auto-refresh if enabled."""
        await super().async_added_to_hass()

        # Start auto-refresh if enabled (uses Home Assistant's event system instead of blocking tasks)
        auto_refresh = self._get_option(CONF_AUTO_REFRESH_ENABLED, DEFAULT_AUTO_REFRESH_ENABLED)
        if auto_refresh:
            interval = datetime.timedelta(minutes=max(1, int(DEFAULT_AUTO_REFRESH_INTERVAL_MINUTES)))
            self._refresh_unsub = async_track_time_interval(
                self.hass,
                self._async_auto_refresh_callback,
                interval
            )
            _LOGGER.debug("Started auto-refresh for %s (interval: %d minutes)", self._name, DEFAULT_AUTO_REFRESH_INTERVAL_MINUTES)

    async def async_will_remove_from_hass(self):
        """Cancel the auto-refresh and clean up PNG file when entity is removed."""
        if self._refresh_unsub:
            self._refresh_unsub()
            self._refresh_unsub = None

        # Only delete the PNG file if the config entry is being removed (not just reloaded)
        from .const import DOMAIN
        is_being_removed = self.hass.data.get(DOMAIN, {}).get(f"{self._entry.entry_id}_removing", False)

        if is_being_removed:
            try:
                if Path(self._path).exists():
                    await self.hass.async_add_executor_job(Path(self._path).unlink)
                    _LOGGER.info("Deleted PNG file for %s: %s", self._name, self._path)
            except Exception as err:
                _LOGGER.warning("Failed to delete PNG file for %s: %s", self._name, err)
        else:
            _LOGGER.debug("Preserving PNG file for %s during reload: %s", self._name, self._path)

    async def _async_auto_refresh_callback(self, now: datetime.datetime) -> None:
        """Callback triggered by Home Assistant's event system for periodic auto-refresh.

        This is called at the configured interval and does not block Home Assistant startup
        or other integrations.
        """
        try:
            _LOGGER.debug("Auto-refresh triggered for %s", self._name)
            await self.async_render_image(width=None, height=None, force_render=False, triggered_by="auto_refresh")
        except Exception as err:
            _LOGGER.error("Failed to auto-refresh %s: %s", self._name, err, exc_info=True)

    async def async_camera_image(self, width=None, height=None):
        """Render the graph if needed and return its bytes."""
        await self.async_render_image(width=width, height=height, force_render=False, triggered_by="camera_access")
        return await self.hass.async_add_executor_job(self.camera_image)

    async def async_render_image(self, width=None, height=None, force_render=True, triggered_by="unknown"):
        """Render the graph.

        Args:
            width: Optional width override for the image
            height: Optional height override for the image
            force_render: If True, bypasses throttling to force immediate render
            triggered_by: Source that triggered the render (action, camera_access, auto_refresh, unknown)
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
            timestamp_str: ISO format timestamp string
            price_val: Price value (will be converted to float)
            start_date: Start date for filtering (None to disable)
            end_date: End date for filtering (None to disable)

        Returns:
            tuple: (datetime, price) or None if invalid/filtered out
        """
        dt_loc = dt_util.as_local(dt_util.parse_datetime(timestamp_str))
        if not dt_loc:
            return None

        # Apply date filter only if date range is configured
        if start_date is not None and end_date is not None:
            if not (start_date <= dt_loc.date() <= end_date):
                return None

        try:
            price = float(price_val)
            return (dt_loc, price)
        except (TypeError, ValueError):
            return None

    def _parse_price_data_from_entity(self):
        """Extract and filter price data from a Home Assistant entity."""
        state = self.hass.states.get(self._price_entity_id)
        if not state:
            _LOGGER.warning("Price entity %s not found for %s", self._price_entity_id, self._name)
            return [], []

        # Try to get prices from 'prices' attribute first, then 'data' attribute
        data = state.attributes.get("prices") or state.attributes.get("data")
        if not data:
            _LOGGER.warning("No price data in entity %s for %s", self._price_entity_id, self._name)
            return [], []

        if not isinstance(data, list):
            _LOGGER.warning("Invalid price data format in entity %s for %s: expected list, got %s",
                          self._price_entity_id, self._name, type(data))
            return [], []

        # Get date range filter
        start_date, end_date = self._get_date_range_filter()

        # Parse price data from entity (same format as local_render.json)
        paired = []
        for item in data:
            if not isinstance(item, dict):
                continue

            # Support `start_time`|`start`|`startsAt` keys (prioritize in that order)
            time_key = item.get("start_time") or item.get("start") or item.get("startsAt")
            # Support `price`|`price_per_kwh`|`total` keys (prioritize in that order)
            price_val = item.get("price") or item.get("price_per_kwh") or item.get("total")

            if not time_key or price_val is None:
                continue

            result = self._parse_datetime_and_price(time_key, price_val, start_date, end_date)
            if result:
                paired.append(result)

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
        for k, v in items:
            result = self._parse_datetime_and_price(k, v, start_date, end_date)
            if result:
                paired.append(result)

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

            # Determine currency to display: override if configured, otherwise auto-select based on cents mode
            currency_override = self._get_option(CONF_CURRENCY_OVERRIDE, DEFAULT_CURRENCY_OVERRIDE)
            use_cents = self._get_option(CONF_USE_CENTS, DEFAULT_USE_CENTS)

            if currency_override:
                currency = currency_override
            elif use_cents:
                currency = "¢"
            else:
                # Get currency from Tibber home if available, otherwise empty string
                currency = self._home.currency if self._home else ""

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
            "show_x_ticks": self._get_option(CONF_SHOW_X_TICKS, DEFAULT_SHOW_X_TICKS),
            "start_graph_at": self._get_option(CONF_START_GRAPH_AT, DEFAULT_START_GRAPH_AT),
            "x_axis_label_y_offset": DEFAULT_X_AXIS_LABEL_Y_OFFSET,
            "x_tick_step_hours": self._get_option(CONF_X_TICK_STEP_HOURS, DEFAULT_X_TICK_STEP_HOURS),
            "hours_to_show": self._get_option(CONF_HOURS_TO_SHOW, DEFAULT_HOURS_TO_SHOW),
            "show_vertical_grid": self._get_option(CONF_SHOW_VERTICAL_GRID, DEFAULT_SHOW_VERTICAL_GRID),
            # Y-axis settings
            "show_y_axis": self._get_option(CONF_SHOW_Y_AXIS, DEFAULT_SHOW_Y_AXIS),
            "show_y_axis_ticks": self._get_option(CONF_SHOW_Y_AXIS_TICKS, DEFAULT_SHOW_Y_AXIS_TICKS),
            "show_horizontal_grid": self._get_option(CONF_SHOW_HORIZONTAL_GRID, DEFAULT_SHOW_HORIZONTAL_GRID),
            "show_average_price_line": self._get_option(CONF_SHOW_AVERAGE_PRICE_LINE, DEFAULT_SHOW_AVERAGE_PRICE_LINE),
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
            "label_current_in_header": self._get_option(CONF_LABEL_CURRENT_IN_HEADER, DEFAULT_LABEL_CURRENT_IN_HEADER),
            "label_current_in_header_more": self._get_option(CONF_LABEL_CURRENT_IN_HEADER_MORE, DEFAULT_LABEL_CURRENT_IN_HEADER_MORE),
            "label_current_in_header_font_weight": DEFAULT_LABEL_CURRENT_IN_HEADER_FONT_WEIGHT,
            "label_current_in_header_padding": DEFAULT_LABEL_CURRENT_IN_HEADER_PADDING,
            "label_font_size": self._get_option(CONF_LABEL_FONT_SIZE, DEFAULT_LABEL_FONT_SIZE),
            "label_font_weight": DEFAULT_LABEL_FONT_WEIGHT,
            "label_max": self._get_option(CONF_LABEL_MAX, DEFAULT_LABEL_MAX),
            "label_max_below_point": DEFAULT_LABEL_MAX_BELOW_POINT,
            "label_min": self._get_option(CONF_LABEL_MIN, DEFAULT_LABEL_MIN),
            "label_minmax_show_price": self._get_option(CONF_LABEL_MINMAX_SHOW_PRICE, DEFAULT_LABEL_MINMAX_SHOW_PRICE),
            "label_show_currency": self._get_option(CONF_LABEL_SHOW_CURRENCY, DEFAULT_LABEL_SHOW_CURRENCY),
            "label_use_colors": self._get_option(CONF_LABEL_USE_COLORS, DEFAULT_LABEL_USE_COLORS),
            "price_decimals": self._get_option(CONF_PRICE_DECIMALS, DEFAULT_PRICE_DECIMALS),
            "color_price_line_by_average": self._get_option(CONF_COLOR_PRICE_LINE_BY_AVERAGE, DEFAULT_COLOR_PRICE_LINE_BY_AVERAGE),
        }
