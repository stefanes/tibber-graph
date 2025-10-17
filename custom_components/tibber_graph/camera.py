"""Camera platform for Tibber Graph component."""
import asyncio
import datetime
import logging
from bisect import bisect_right
from pathlib import Path

from homeassistant.components.local_file.camera import LocalFile
from homeassistant.util import dt as dt_util

# Import configuration - try config.py first, fall back to defaults.py if not present
try:
    from .config import *
except (ImportError, FileNotFoundError):
    from .defaults import *

from .renderer import render_plot_to_path

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Tibber Graph camera platform."""
    Path(hass.config.path("www/")).mkdir(parents=True, exist_ok=True)
    entities = []
    for home in hass.data["tibber"].get_homes(only_active=True):
        if not home.info:
            await home.update_info()
        entities.append(TibberCam(home, hass))

    _LOGGER.info("Setting up %d Tibber Graph camera(s)", len(entities))
    async_add_entities(entities)


class TibberCam(LocalFile):
    """Camera entity that generates a dynamic Tibber price graph image."""

    def __init__(self, home, hass):
        """Initialize the Tibber Graph camera."""
        self._name = f"Tibber Graph {home.info['viewer']['home']['appNickname'] or home.info['viewer']['home']['address'].get('address1', '')}"
        name_sanitized = self._name.lower().replace(" ", "_")
        self._path = hass.config.path(f"www/{name_sanitized}.png")
        self._home = home
        self.hass = hass
        self._last_update = dt_util.now() - datetime.timedelta(hours=1)
        self._render_lock = asyncio.Lock()
        self._uniqueid = f"camera_{name_sanitized}"
        self._refresh_task = None
        super().__init__(self._name, self._path, self._uniqueid)

        # Start auto-refresh task if enabled
        if AUTO_REFRESH_ENABLED:
            self._refresh_task = self.hass.async_create_task(self._auto_refresh_loop())
            _LOGGER.debug("Initialized %s with auto-refresh every %d minutes", self._name, AUTO_REFRESH_INTERVAL_MINUTES)

    async def async_will_remove_from_hass(self):
        """Cancel the auto-refresh task when entity is removed."""
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass

    async def _auto_refresh_loop(self):
        """Background task that automatically refreshes the chart at a configurable interval."""
        try:
            while True:
                now = dt_util.now()
                interval = max(1, int(AUTO_REFRESH_INTERVAL_MINUTES))
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
        if FORCE_FIXED_SIZE:
            w, h = CANVAS_WIDTH, CANVAS_HEIGHT
        else:
            w = width or CANVAS_WIDTH
            h = height or CANVAS_HEIGHT
        await self._generate_fig(w, h)
        return await self.hass.async_add_executor_job(self.camera_image)

    def _parse_price_data(self):
        """Extract and filter price data for the configured range."""
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
        if USE_HOURLY_PRICES:
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
        hourly_dates = sorted_hours
        hourly_prices = [sum(hourly_data[h]) / len(hourly_data[h]) for h in sorted_hours]

        return hourly_dates, hourly_prices

    async def _generate_fig(self, width, height):
        """Throttle and trigger figure rendering in background."""
        async with self._render_lock:
            now = dt_util.now()
            if (now - self._last_update).total_seconds() < MIN_REDRAW_INTERVAL_SECONDS:
                return

            try:
                if (self._home.last_data_timestamp - now).total_seconds() > 11 * 3600:
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
            step_minutes = int((dates[1] - dates[0]).total_seconds() // 60) or (60 if USE_HOURLY_PRICES else 15)
            interval_td = datetime.timedelta(minutes=step_minutes)
            dates_plot = list(dates) + [dates[-1] + interval_td]
            prices_plot = list(prices) + [prices[-1]]

            now_local = dt_util.as_local(dt_util.now())
            idx = bisect_right(dates, now_local) - 1
            idx = max(0, min(idx, len(prices) - 1))

            # Determine currency to display: override if configured, otherwise use Tibber home currency
            currency = CURRENCY_OVERRIDE if CURRENCY_OVERRIDE else (self._home.currency or "")

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
                )
                _LOGGER.debug("Rendered chart for %s", self._name)
            except Exception as err:
                _LOGGER.error("Failed to render chart for %s: %s", self._name, err, exc_info=True)
                raise
