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
    CONF_ENTITY_NAME,
    # General config keys
    CONF_THEME,
    CONF_CANVAS_WIDTH,
    CONF_CANVAS_HEIGHT,
    CONF_FORCE_FIXED_SIZE,
    # X-axis config keys
    CONF_SHOW_X_TICKS,
    CONF_START_AT_MIDNIGHT,
    CONF_X_AXIS_LABEL_ROTATION_DEG,
    CONF_X_TICK_STEP_HOURS,
    CONF_HOURS_TO_SHOW,
    CONF_SHOW_VERTICAL_GRID,
    # Y-axis config keys
    CONF_SHOW_Y_AXIS,
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
    DEFAULT_ENTITY_NAME,
    # General defaults
    DEFAULT_THEME,
    DEFAULT_CANVAS_WIDTH,
    DEFAULT_CANVAS_HEIGHT,
    DEFAULT_FORCE_FIXED_SIZE,
    # X-axis defaults
    DEFAULT_SHOW_X_TICKS,
    DEFAULT_START_AT_MIDNIGHT,
    DEFAULT_X_AXIS_LABEL_ROTATION_DEG,
    DEFAULT_X_TICK_STEP_HOURS,
    DEFAULT_HOURS_TO_SHOW,
    DEFAULT_SHOW_VERTICAL_GRID,
    # Y-axis defaults
    DEFAULT_SHOW_Y_AXIS,
    DEFAULT_SHOW_HORIZONTAL_GRID,
    DEFAULT_SHOW_AVERAGE_PRICE_LINE,
    DEFAULT_CHEAP_PRICE_POINTS,
    DEFAULT_Y_AXIS_LABEL_ROTATION_DEG,
    DEFAULT_Y_AXIS_SIDE,
    DEFAULT_Y_TICK_COUNT,
    DEFAULT_Y_TICK_USE_COLORS,
    # Price label defaults
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
    # Refresh defaults
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

        errors = {}

        if user_input is not None:
            # Generate a unique entity name if not provided
            entity_name = user_input.get(CONF_ENTITY_NAME, "").strip()
            if not entity_name:
                # Auto-generate entity name based on Tibber home
                try:
                    homes = self.hass.data["tibber"].get_homes(only_active=True)
                    if homes:
                        home = homes[0]
                        if not home.info:
                            await home.update_info()
                        entity_name = home.info['viewer']['home']['appNickname'] or home.info['viewer']['home']['address'].get('address1', 'Tibber Graph')
                except Exception:
                    entity_name = "Tibber Graph"

            user_input[CONF_ENTITY_NAME] = entity_name

            # Check for duplicate entity names
            existing_entries = self._async_current_entries()
            for entry in existing_entries:
                if entry.data.get(CONF_ENTITY_NAME) == entity_name:
                    errors["entity_name"] = "entity_name_exists"
                    break

            if not errors:
                # Use entity name as title (without prefix - prefix is added to camera entity name)
                title = entity_name
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_ENTITY_NAME, default=""): cv.string,
                    vol.Optional(
                        CONF_THEME, default=DEFAULT_THEME
                    ): vol.In(["dark", "light"]),
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of nullable fields."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if user_input is not None:
            # Check if "reset all" was selected
            if user_input.get("reset_all", False):
                # Reset all options to defaults (clear all options)
                updated_options = {}
            else:
                # Merge user input with existing options, resetting checked fields to defaults
                updated_options = dict(entry.options)

                # Reset only the fields that were checked
                if user_input.get(f"reset_{CONF_HOURS_TO_SHOW}", False):
                    if CONF_HOURS_TO_SHOW in updated_options:
                        del updated_options[CONF_HOURS_TO_SHOW]

                if user_input.get(f"reset_{CONF_Y_TICK_COUNT}", False):
                    if CONF_Y_TICK_COUNT in updated_options:
                        del updated_options[CONF_Y_TICK_COUNT]

                if user_input.get(f"reset_{CONF_PRICE_DECIMALS}", False):
                    if CONF_PRICE_DECIMALS in updated_options:
                        del updated_options[CONF_PRICE_DECIMALS]

                if user_input.get(f"reset_{CONF_CURRENCY_OVERRIDE}", False):
                    if CONF_CURRENCY_OVERRIDE in updated_options:
                        del updated_options[CONF_CURRENCY_OVERRIDE]

            return self.async_update_reload_and_abort(
                entry,
                data=entry.data,
                options=updated_options,
            )

        # Show form with checkboxes for resetting fields
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._get_reconfigure_schema(),
        )

    def _get_reconfigure_schema(self) -> vol.Schema:
        """Return schema for reconfiguring nullable fields only."""
        return vol.Schema(
            {
                vol.Optional(
                    f"reset_{CONF_HOURS_TO_SHOW}",
                    default=False,
                ): cv.boolean,
                vol.Optional(
                    f"reset_{CONF_Y_TICK_COUNT}",
                    default=False,
                ): cv.boolean,
                vol.Optional(
                    f"reset_{CONF_PRICE_DECIMALS}",
                    default=False,
                ): cv.boolean,
                vol.Optional(
                    f"reset_{CONF_CURRENCY_OVERRIDE}",
                    default=False,
                ): cv.boolean,
                vol.Optional(
                    "reset_all",
                    default=False,
                ): cv.boolean,
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return TibberGraphOptionsFlowHandler()


class TibberGraphOptionsFlowHandler(config_entries.OptionsFlowWithReload):
    """Handle options flow for Tibber Graph."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
        )

    def _get_options_schema(self) -> vol.Schema:
        """Return the options schema."""
        options = self.config_entry.options
        # Fallback to entry.data for initial values (e.g., theme set during setup)
        data = self.config_entry.data

        return vol.Schema(
            {
                # General settings
                vol.Optional(
                    CONF_THEME,
                    default=options.get(CONF_THEME, data.get(CONF_THEME, DEFAULT_THEME)),
                ): vol.In(["dark", "light"]),
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
                vol.Optional(
                    CONF_HOURS_TO_SHOW,
                    default=options.get(CONF_HOURS_TO_SHOW, DEFAULT_HOURS_TO_SHOW),
                ): vol.Any(None, cv.positive_int),
                vol.Optional(
                    CONF_SHOW_VERTICAL_GRID,
                    default=options.get(CONF_SHOW_VERTICAL_GRID, DEFAULT_SHOW_VERTICAL_GRID),
                ): cv.boolean,
                # Y-axis settings
                vol.Optional(
                    CONF_SHOW_Y_AXIS,
                    default=options.get(CONF_SHOW_Y_AXIS, DEFAULT_SHOW_Y_AXIS),
                ): cv.boolean,
                vol.Optional(
                    CONF_SHOW_HORIZONTAL_GRID,
                    default=options.get(CONF_SHOW_HORIZONTAL_GRID, DEFAULT_SHOW_HORIZONTAL_GRID),
                ): cv.boolean,
                vol.Optional(
                    CONF_SHOW_AVERAGE_PRICE_LINE,
                    default=options.get(CONF_SHOW_AVERAGE_PRICE_LINE, DEFAULT_SHOW_AVERAGE_PRICE_LINE),
                ): cv.boolean,
                vol.Optional(
                    CONF_CHEAP_PRICE_POINTS,
                    default=options.get(CONF_CHEAP_PRICE_POINTS, DEFAULT_CHEAP_PRICE_POINTS),
                ): cv.positive_int,
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
                vol.Optional(
                    CONF_COLOR_PRICE_LINE_BY_AVERAGE,
                    default=options.get(CONF_COLOR_PRICE_LINE_BY_AVERAGE, DEFAULT_COLOR_PRICE_LINE_BY_AVERAGE),
                ): cv.boolean,
                # Refresh settings
                vol.Optional(
                    CONF_AUTO_REFRESH_ENABLED,
                    default=options.get(CONF_AUTO_REFRESH_ENABLED, DEFAULT_AUTO_REFRESH_ENABLED),
                ): cv.boolean,
            }
        )
