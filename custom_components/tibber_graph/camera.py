"""Camera platform for Tibber Graph component."""
from __future__ import annotations

import asyncio
import datetime
import logging
from bisect import bisect_right
from pathlib import Path
from typing import Any

from homeassistant.components.local_file.camera import LocalFile
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    # General config keys
    CONF_ENTITY_NAME,
    CONF_PRICE_ENTITY_ID,
    CONF_THEME,
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
    CONF_Y_AXIS_LABEL_ROTATION_DEG,
    CONF_Y_AXIS_SIDE,
    CONF_Y_TICK_COUNT,
    CONF_Y_TICK_USE_COLORS,
    # Price label config keys
    CONF_USE_HOURLY_PRICES,
    CONF_USE_CENTS,
    CONF_CURRENCY_OVERRIDE,
    CONF_LABEL_CURRENT,
    CONF_LABEL_CURRENT_AT_TOP,
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
    DEFAULT_Y_AXIS_LABEL_ROTATION_DEG,
    DEFAULT_Y_AXIS_SIDE,
    DEFAULT_Y_TICK_COUNT,
    DEFAULT_Y_TICK_USE_COLORS,
    DEFAULT_USE_HOURLY_PRICES,
    DEFAULT_USE_CENTS,
    DEFAULT_CURRENCY_OVERRIDE,
    DEFAULT_LABEL_CURRENT,
    DEFAULT_LABEL_CURRENT_AT_TOP,
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
    DEFAULT_LABEL_CURRENT_AT_TOP_FONT_WEIGHT,
    DEFAULT_LABEL_CURRENT_AT_TOP_PADDING,
    DEFAULT_LABEL_FONT_WEIGHT,
    DEFAULT_LABEL_MAX_BELOW_POINT,
    DEFAULT_AUTO_REFRESH_INTERVAL_MINUTES,
    DEFAULT_MIN_REDRAW_INTERVAL_SECONDS,
)

from .renderer import render_plot_to_path

_LOGGER = logging.getLogger(__name__)


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
        self._refresh_task = None
        super().__init__(self._name, self._path, self._uniqueid)

        # Migrate old "start_at_midnight" boolean option to new "start_graph_at" dropdown
        self._migrate_start_graph_at_option()

        # Migrate old "dark_black" theme to "dark" with transparent background
        self._migrate_dark_black_theme()

        # Start auto-refresh task if enabled
        auto_refresh = self._get_option(CONF_AUTO_REFRESH_ENABLED, DEFAULT_AUTO_REFRESH_ENABLED)
        if auto_refresh:
            self._refresh_task = self.hass.async_create_task(self._auto_refresh_loop())
            _LOGGER.debug("Initialized %s with auto-refresh every %d minutes", self._name, DEFAULT_AUTO_REFRESH_INTERVAL_MINUTES)

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

    def _migrate_start_graph_at_option(self):
        """Migrate old 'start_at_midnight' boolean option to new 'start_graph_at' dropdown.

        This method converts the deprecated boolean option to the new dropdown format:
        - start_at_midnight=True → start_graph_at="midnight"
        - start_at_midnight=False → start_graph_at="current_hour"

        The migration is performed only once when the old option exists.
        After migration, the old option is removed from the config entry.
        """
        if not self._entry:
            return

        # Check if old option exists in either options or data
        old_key = "start_at_midnight"
        has_old_option = False
        old_value = None

        # Check options first (priority)
        if self._options and old_key in self._options:
            has_old_option = True
            old_value = self._options[old_key]
            location = "options"
        # Then check entry.data
        elif old_key in self._entry.data:
            has_old_option = True
            old_value = self._entry.data[old_key]
            location = "data"

        # Only migrate if old option exists and new option doesn't
        if has_old_option and CONF_START_GRAPH_AT not in (self._options or {}):
            # Convert boolean to new dropdown value
            new_value = START_GRAPH_AT_MIDNIGHT if old_value else START_GRAPH_AT_CURRENT_HOUR

            _LOGGER.info(
                "Migrating %s option for %s: start_at_midnight=%s → start_graph_at=%s",
                location, self._name, old_value, new_value
            )

            # Update the config entry with new option and remove old one
            new_options = dict(self._options) if self._options else {}
            new_options[CONF_START_GRAPH_AT] = new_value

            # Remove old option from the dict we're updating
            if old_key in new_options:
                del new_options[old_key]

            # Update the config entry
            self.hass.config_entries.async_update_entry(
                self._entry,
                options=new_options
            )

            # Update local reference
            self._options = new_options

    def _migrate_dark_black_theme(self):
        """Migrate old 'dark_black' theme to 'dark' with transparent background.

        This method converts the deprecated dark_black theme to the new format:
        - theme="dark_black" → theme="dark" + transparent_background=True

        The migration is performed only once when the old theme value exists.
        After migration, the theme is updated and transparent_background is set.
        """
        if not self._entry:
            return

        # Check if theme is set to dark_black in either options or data
        has_dark_black = False
        location = None

        # Check options first (priority)
        if self._options and self._options.get(CONF_THEME) == "dark_black":
            has_dark_black = True
            location = "options"
        # Then check entry.data
        elif self._entry.data.get(CONF_THEME) == "dark_black":
            has_dark_black = True
            location = "data"

        # Only migrate if dark_black theme is found
        if has_dark_black:
            _LOGGER.info(
                "Migrating %s for %s: theme='dark_black' → theme='dark' + transparent_background=True",
                location, self._name
            )

            # Update the config entry
            new_options = dict(self._options) if self._options else {}
            new_data = dict(self._entry.data)

            # Set theme to dark and enable transparent background
            if location == "options":
                new_options[CONF_THEME] = "dark"
                new_options[CONF_TRANSPARENT_BACKGROUND] = True
            else:  # location == "data"
                new_data[CONF_THEME] = "dark"
                # Add transparent background to options if not already there
                if CONF_TRANSPARENT_BACKGROUND not in new_options:
                    new_options[CONF_TRANSPARENT_BACKGROUND] = True

            # Update the config entry
            self.hass.config_entries.async_update_entry(
                self._entry,
                data=new_data,
                options=new_options
            )

            # Update local references
            self._options = new_options

    async def async_will_remove_from_hass(self):
        """Cancel the auto-refresh task and clean up PNG file when entity is removed."""
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass

        # Delete the PNG file from www directory
        try:
            if Path(self._path).exists():
                await self.hass.async_add_executor_job(Path(self._path).unlink)
                _LOGGER.info("Deleted PNG file for %s: %s", self._name, self._path)
        except Exception as err:
            _LOGGER.warning("Failed to delete PNG file for %s: %s", self._name, err)

    async def _auto_refresh_loop(self):
        """Background task that automatically refreshes the chart at a configurable interval."""
        try:
            while True:
                now = dt_util.now()
                interval = max(1, int(DEFAULT_AUTO_REFRESH_INTERVAL_MINUTES))
                # Calculate time until next interval mark (e.g., every 10 minutes: 12:00, 12:10, 12:20, ...)
                next_tick = (now + datetime.timedelta(minutes=interval - now.minute % interval)).replace(second=0, microsecond=0)
                sleep_seconds = (next_tick - now).total_seconds()
                await asyncio.sleep(sleep_seconds)
                try:
                    await self.async_camera_image()
                except Exception as err:
                    _LOGGER.error("Failed to auto-refresh %s: %s", self._name, err, exc_info=True)
        except asyncio.CancelledError:
            _LOGGER.debug("Stopped auto-refresh for %s", self._name)
            raise

    async def async_camera_image(self, width=None, height=None):
        """Render the chart image if needed and return its bytes."""
        force_fixed = self._get_option(CONF_FORCE_FIXED_SIZE, DEFAULT_FORCE_FIXED_SIZE)
        canvas_width = self._get_option(CONF_CANVAS_WIDTH, DEFAULT_CANVAS_WIDTH)
        canvas_height = self._get_option(CONF_CANVAS_HEIGHT, DEFAULT_CANVAS_HEIGHT)

        if force_fixed:
            w, h = canvas_width, canvas_height
        else:
            w = width or canvas_width
            h = height or canvas_height
        await self._generate_fig(w, h)
        return await self.hass.async_add_executor_job(self.camera_image)

    def _parse_price_data(self):
        """Extract and filter price data for the configured range."""
        # Check if using entity or Tibber integration
        if self._price_entity_id:
            return self._parse_price_data_from_entity()
        else:
            return self._parse_price_data_from_tibber()

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

        # Pre-calculate date range once
        now_local = dt_util.as_local(dt_util.now())
        start_date = now_local.date()
        end_date = start_date + datetime.timedelta(days=1)

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

            dt_loc = dt_util.as_local(dt_util.parse_datetime(time_key))
            if not dt_loc or not (start_date <= dt_loc.date() <= end_date):
                continue
            try:
                price = float(price_val)
                paired.append((dt_loc, price))
            except (TypeError, ValueError):
                continue

        if not paired:
            _LOGGER.warning("No valid price data in date range from entity %s for %s",
                          self._price_entity_id, self._name)
            return [], []

        # Sort once
        paired.sort(key=lambda x: x[0])
        dates, prices = zip(*paired)
        dates, prices = list(dates), list(prices)

        # Aggregate to hourly prices if configured
        use_hourly = self._get_option(CONF_USE_HOURLY_PRICES, DEFAULT_USE_HOURLY_PRICES)
        if use_hourly:
            dates, prices = self._aggregate_to_hourly(dates, prices)

        _LOGGER.debug("Parsed %d price data points from entity for %s", len(prices), self._name)
        return dates, prices

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

        # Pre-calculate date range once
        now_local = dt_util.as_local(dt_util.now())
        start_date = now_local.date()
        end_date = start_date + datetime.timedelta(days=1)

        # Build and sort in one pass - avoid building intermediate lists
        paired = []
        for k, v in items:
            dt_loc = dt_util.as_local(dt_util.parse_datetime(k))
            if not dt_loc or not (start_date <= dt_loc.date() <= end_date):
                continue
            try:
                price = float(v)
                paired.append((dt_loc, price))
            except (TypeError, ValueError):
                continue

        if not paired:
            _LOGGER.warning("No valid price data in date range for %s", self._name)
            return [], []

        # Sort once
        paired.sort(key=lambda x: x[0])
        dates, prices = zip(*paired)
        dates, prices = list(dates), list(prices)

        # Aggregate to hourly prices if configured
        use_hourly = self._get_option(CONF_USE_HOURLY_PRICES, DEFAULT_USE_HOURLY_PRICES)
        if use_hourly:
            dates, prices = self._aggregate_to_hourly(dates, prices)

        _LOGGER.debug("Parsed %d price data points for %s", len(prices), self._name)
        return dates, prices

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

    async def _generate_fig(self, width, height):
        """Throttle and trigger figure rendering in background."""
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
                _LOGGER.warning("Insufficient price data (%d points) to render chart for %s", len(prices), self._name)
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

            try:
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
                )
                _LOGGER.debug("Rendered chart for %s", self._name)
            except Exception as err:
                _LOGGER.error("Failed to render chart for %s: %s", self._name, err, exc_info=True)
                raise

    def _get_render_options(self) -> dict[str, Any]:
        """Collect rendering options from config entry (UI) or defaults.py."""
        return {
            # General settings
            "theme": self._get_option(CONF_THEME, DEFAULT_THEME),
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
            "label_current_at_top": self._get_option(CONF_LABEL_CURRENT_AT_TOP, DEFAULT_LABEL_CURRENT_AT_TOP),
            "label_current_at_top_font_weight": DEFAULT_LABEL_CURRENT_AT_TOP_FONT_WEIGHT,
            "label_current_at_top_padding": DEFAULT_LABEL_CURRENT_AT_TOP_PADDING,
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
