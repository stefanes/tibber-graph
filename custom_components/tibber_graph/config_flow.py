"""Config flow for Tibber Graph integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    # General
    CONF_THEME,
    CONF_CANVAS_WIDTH,
    CONF_CANVAS_HEIGHT,
    CONF_FORCE_FIXED_SIZE,
    # X-axis
    CONF_SHOW_X_TICKS,
    CONF_START_AT_MIDNIGHT,
    CONF_X_AXIS_LABEL_ROTATION_DEG,
    CONF_X_TICK_STEP_HOURS,
    # Y-axis
    CONF_SHOW_Y_AXIS,
    CONF_SHOW_Y_GRID,
    CONF_Y_AXIS_LABEL_ROTATION_DEG,
    CONF_Y_AXIS_SIDE,
    CONF_Y_TICK_COUNT,
    CONF_Y_TICK_USE_COLORS,
    # Price labels
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
    # Refresh
    CONF_AUTO_REFRESH_ENABLED,
    # Defaults - General
    DEFAULT_THEME,
    DEFAULT_CANVAS_WIDTH,
    DEFAULT_CANVAS_HEIGHT,
    DEFAULT_FORCE_FIXED_SIZE,
    # Defaults - X-axis
    DEFAULT_SHOW_X_TICKS,
    DEFAULT_START_AT_MIDNIGHT,
    DEFAULT_X_AXIS_LABEL_ROTATION_DEG,
    DEFAULT_X_TICK_STEP_HOURS,
    # Defaults - Y-axis
    DEFAULT_SHOW_Y_AXIS,
    DEFAULT_SHOW_Y_GRID,
    DEFAULT_Y_AXIS_LABEL_ROTATION_DEG,
    DEFAULT_Y_AXIS_SIDE,
    DEFAULT_Y_TICK_COUNT,
    DEFAULT_Y_TICK_USE_COLORS,
    # Defaults - Price labels
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
    # Defaults - Refresh
    DEFAULT_AUTO_REFRESH_ENABLED,
)

_LOGGER = logging.getLogger(__name__)


class TibberGraphConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tibber Graph."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Check if Tibber integration is set up
        if "tibber" not in self.hass.config.components:
            return self.async_abort(reason="tibber_not_setup")

        if user_input is not None:
            return self.async_create_entry(title="Tibber Graph", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_THEME, default=DEFAULT_THEME
                    ): vol.In(["light", "dark"]),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> TibberGraphOptionsFlowHandler:
        """Get the options flow for this handler."""
        return TibberGraphOptionsFlowHandler(config_entry)


class TibberGraphOptionsFlowHandler(config_entries.OptionsFlowWithReload):
    """Handle options flow for Tibber Graph."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Validate and clean up user input
            _LOGGER.debug("Saving options: %s", user_input)
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
        )

    def _get_options_schema(self) -> vol.Schema:
        """Return the options schema."""
        options = self.config_entry.options

        return vol.Schema(
            {
                # General settings
                vol.Optional(
                    CONF_THEME,
                    default=options.get(CONF_THEME, DEFAULT_THEME),
                ): vol.In(["light", "dark"]),
                vol.Optional(
                    CONF_CANVAS_WIDTH,
                    default=options.get(CONF_CANVAS_WIDTH, DEFAULT_CANVAS_WIDTH),
                ): cv.positive_int,
                vol.Optional(
                    CONF_CANVAS_HEIGHT,
                    default=options.get(CONF_CANVAS_HEIGHT, DEFAULT_CANVAS_HEIGHT),
                ): cv.positive_int,
                vol.Optional(
                    CONF_FORCE_FIXED_SIZE,
                    default=options.get(CONF_FORCE_FIXED_SIZE, DEFAULT_FORCE_FIXED_SIZE),
                ): cv.boolean,
                # X-axis settings
                vol.Optional(
                    CONF_SHOW_X_TICKS,
                    default=options.get(CONF_SHOW_X_TICKS, DEFAULT_SHOW_X_TICKS),
                ): cv.boolean,
                vol.Optional(
                    CONF_START_AT_MIDNIGHT,
                    default=options.get(CONF_START_AT_MIDNIGHT, DEFAULT_START_AT_MIDNIGHT),
                ): cv.boolean,
                vol.Optional(
                    CONF_X_AXIS_LABEL_ROTATION_DEG,
                    default=options.get(CONF_X_AXIS_LABEL_ROTATION_DEG, DEFAULT_X_AXIS_LABEL_ROTATION_DEG),
                ): cv.positive_int,
                vol.Optional(
                    CONF_X_TICK_STEP_HOURS,
                    default=options.get(CONF_X_TICK_STEP_HOURS, DEFAULT_X_TICK_STEP_HOURS),
                ): cv.positive_int,
                # Y-axis settings
                vol.Optional(
                    CONF_SHOW_Y_AXIS,
                    default=options.get(CONF_SHOW_Y_AXIS, DEFAULT_SHOW_Y_AXIS),
                ): cv.boolean,
                vol.Optional(
                    CONF_SHOW_Y_GRID,
                    default=options.get(CONF_SHOW_Y_GRID, DEFAULT_SHOW_Y_GRID),
                ): cv.boolean,
                vol.Optional(
                    CONF_Y_AXIS_LABEL_ROTATION_DEG,
                    default=options.get(CONF_Y_AXIS_LABEL_ROTATION_DEG, DEFAULT_Y_AXIS_LABEL_ROTATION_DEG),
                ): cv.positive_int,
                vol.Optional(
                    CONF_Y_AXIS_SIDE,
                    default=options.get(CONF_Y_AXIS_SIDE, DEFAULT_Y_AXIS_SIDE),
                ): vol.In(["left", "right"]),
                vol.Optional(
                    CONF_Y_TICK_COUNT,
                    default=options.get(CONF_Y_TICK_COUNT, DEFAULT_Y_TICK_COUNT),
                ): vol.Any(None, cv.positive_int),
                vol.Optional(
                    CONF_Y_TICK_USE_COLORS,
                    default=options.get(CONF_Y_TICK_USE_COLORS, DEFAULT_Y_TICK_USE_COLORS),
                ): cv.boolean,
                # Price labels
                vol.Optional(
                    CONF_USE_HOURLY_PRICES,
                    default=options.get(CONF_USE_HOURLY_PRICES, DEFAULT_USE_HOURLY_PRICES),
                ): cv.boolean,
                vol.Optional(
                    CONF_USE_CENTS,
                    default=options.get(CONF_USE_CENTS, DEFAULT_USE_CENTS),
                ): cv.boolean,
                vol.Optional(
                    CONF_CURRENCY_OVERRIDE,
                    default=options.get(CONF_CURRENCY_OVERRIDE, DEFAULT_CURRENCY_OVERRIDE or ""),
                ): cv.string,
                vol.Optional(
                    CONF_LABEL_CURRENT,
                    default=options.get(CONF_LABEL_CURRENT, DEFAULT_LABEL_CURRENT),
                ): cv.boolean,
                vol.Optional(
                    CONF_LABEL_CURRENT_AT_TOP,
                    default=options.get(CONF_LABEL_CURRENT_AT_TOP, DEFAULT_LABEL_CURRENT_AT_TOP),
                ): cv.boolean,
                vol.Optional(
                    CONF_LABEL_FONT_SIZE,
                    default=options.get(CONF_LABEL_FONT_SIZE, DEFAULT_LABEL_FONT_SIZE),
                ): cv.positive_int,
                vol.Optional(
                    CONF_LABEL_MAX,
                    default=options.get(CONF_LABEL_MAX, DEFAULT_LABEL_MAX),
                ): cv.boolean,
                vol.Optional(
                    CONF_LABEL_MIN,
                    default=options.get(CONF_LABEL_MIN, DEFAULT_LABEL_MIN),
                ): cv.boolean,
                vol.Optional(
                    CONF_LABEL_MINMAX_SHOW_PRICE,
                    default=options.get(CONF_LABEL_MINMAX_SHOW_PRICE, DEFAULT_LABEL_MINMAX_SHOW_PRICE),
                ): cv.boolean,
                vol.Optional(
                    CONF_LABEL_SHOW_CURRENCY,
                    default=options.get(CONF_LABEL_SHOW_CURRENCY, DEFAULT_LABEL_SHOW_CURRENCY),
                ): cv.boolean,
                vol.Optional(
                    CONF_LABEL_USE_COLORS,
                    default=options.get(CONF_LABEL_USE_COLORS, DEFAULT_LABEL_USE_COLORS),
                ): cv.boolean,
                vol.Optional(
                    CONF_PRICE_DECIMALS,
                    default=options.get(CONF_PRICE_DECIMALS, DEFAULT_PRICE_DECIMALS),
                ): vol.Any(None, cv.positive_int),
                # Refresh settings
                vol.Optional(
                    CONF_AUTO_REFRESH_ENABLED,
                    default=options.get(CONF_AUTO_REFRESH_ENABLED, DEFAULT_AUTO_REFRESH_ENABLED),
                ): cv.boolean,
            }
        )
