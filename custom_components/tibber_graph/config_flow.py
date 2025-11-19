"""Config flow for Tibber Graph integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv, entity_registry as er, selector

from .themes import get_theme_names
from .helpers import validate_sensor_entity
from .const import (
    DOMAIN,
    CONF_ENTITY_NAME,
    CONF_PRICE_ENTITY_ID,
    # Start graph at options
    START_GRAPH_AT_MIDNIGHT,
    START_GRAPH_AT_CURRENT_HOUR,
    START_GRAPH_AT_SHOW_ALL,
    # Label current options
    LABEL_CURRENT_ON,
    LABEL_CURRENT_ON_CURRENT_PRICE_ONLY,
    LABEL_CURRENT_ON_IN_GRAPH,
    LABEL_CURRENT_ON_IN_GRAPH_NO_PRICE,
    LABEL_CURRENT_OFF,
    # Show X-axis options
    SHOW_X_AXIS_ON,
    SHOW_X_AXIS_ON_WITH_TICK_MARKS,
    SHOW_X_AXIS_OFF,
    # Show Y-axis options
    SHOW_Y_AXIS_ON,
    SHOW_Y_AXIS_ON_WITH_TICK_MARKS,
    SHOW_Y_AXIS_OFF,
    # Label max/min options
    LABEL_MAX_ON,
    LABEL_MAX_ON_NO_PRICE,
    LABEL_MAX_OFF,
    LABEL_MIN_ON,
    LABEL_MIN_ON_NO_PRICE,
    LABEL_MIN_OFF,
    # General config keys
    CONF_THEME,
    CONF_TRANSPARENT_BACKGROUND,
    CONF_CANVAS_WIDTH,
    CONF_CANVAS_HEIGHT,
    CONF_FORCE_FIXED_SIZE,
    CONF_CHEAP_PRICE_POINTS,
    CONF_CHEAP_PRICE_THRESHOLD,
    # X-axis config keys
    CONF_SHOW_X_AXIS,
    CONF_CHEAP_PERIODS_ON_X_AXIS,
    CONF_START_GRAPH_AT,
    CONF_X_TICK_STEP_HOURS,
    CONF_HOURS_TO_SHOW,
    CONF_SHOW_VERTICAL_GRID,
    # Cheap periods on X-axis options
    CHEAP_PERIODS_ON_X_AXIS_ON,
    CHEAP_PERIODS_ON_X_AXIS_ON_COMFY,
    CHEAP_PERIODS_ON_X_AXIS_ON_COMPACT,
    CHEAP_PERIODS_ON_X_AXIS_OFF,
    # Y-axis config keys
    CONF_SHOW_Y_AXIS,
    CONF_SHOW_HORIZONTAL_GRID,
    CONF_SHOW_AVERAGE_PRICE_LINE,
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
    DEFAULT_ENTITY_NAME,
    # General defaults
    DEFAULT_THEME,
    DEFAULT_TRANSPARENT_BACKGROUND,
    DEFAULT_CANVAS_WIDTH,
    DEFAULT_CANVAS_HEIGHT,
    DEFAULT_FORCE_FIXED_SIZE,
    DEFAULT_CHEAP_PRICE_POINTS,
    DEFAULT_CHEAP_PRICE_THRESHOLD,
    # X-axis defaults
    DEFAULT_SHOW_X_AXIS,
    DEFAULT_CHEAP_PERIODS_ON_X_AXIS,
    DEFAULT_START_GRAPH_AT,
    DEFAULT_X_TICK_STEP_HOURS,
    DEFAULT_HOURS_TO_SHOW,
    DEFAULT_SHOW_VERTICAL_GRID,
    # Y-axis defaults
    DEFAULT_SHOW_Y_AXIS,
    DEFAULT_SHOW_HORIZONTAL_GRID,
    DEFAULT_SHOW_AVERAGE_PRICE_LINE,
    DEFAULT_Y_AXIS_LABEL_ROTATION_DEG,
    DEFAULT_Y_AXIS_SIDE,
    DEFAULT_Y_TICK_COUNT,
    DEFAULT_Y_TICK_USE_COLORS,
    # Price label defaults
    DEFAULT_USE_HOURLY_PRICES,
    DEFAULT_USE_CENTS,
    DEFAULT_CURRENCY_OVERRIDE,
    DEFAULT_LABEL_CURRENT,
    DEFAULT_LABEL_FONT_SIZE,
    DEFAULT_LABEL_MAX,
    DEFAULT_LABEL_MIN,
    DEFAULT_LABEL_SHOW_CURRENCY,
    DEFAULT_LABEL_USE_COLORS,
    DEFAULT_PRICE_DECIMALS,
    DEFAULT_COLOR_PRICE_LINE_BY_AVERAGE,
    # Refresh defaults
    DEFAULT_REFRESH_MODE,
    # Refresh mode options
    REFRESH_MODE_SYSTEM,
    REFRESH_MODE_SYSTEM_INTERVAL,
    REFRESH_MODE_INTERVAL,
    REFRESH_MODE_MANUAL,
)

_LOGGER = logging.getLogger(__name__)

# Shared theme selector configuration - dynamically load available themes
THEME_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=get_theme_names(),
        mode=selector.SelectSelectorMode.DROPDOWN,
        translation_key="theme",
    )
)

# Start graph at selector configuration
START_GRAPH_AT_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=[START_GRAPH_AT_MIDNIGHT, START_GRAPH_AT_CURRENT_HOUR, START_GRAPH_AT_SHOW_ALL],
        mode=selector.SelectSelectorMode.DROPDOWN,
        translation_key="start_graph_at",
    )
)

# Label current selector configuration
LABEL_CURRENT_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=[LABEL_CURRENT_ON, LABEL_CURRENT_ON_CURRENT_PRICE_ONLY, LABEL_CURRENT_ON_IN_GRAPH, LABEL_CURRENT_ON_IN_GRAPH_NO_PRICE, LABEL_CURRENT_OFF],
        mode=selector.SelectSelectorMode.DROPDOWN,
        translation_key="label_current",
    )
)

# Show X-axis selector configuration
SHOW_X_AXIS_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=[SHOW_X_AXIS_ON, SHOW_X_AXIS_ON_WITH_TICK_MARKS, SHOW_X_AXIS_OFF],
        mode=selector.SelectSelectorMode.DROPDOWN,
        translation_key="show_x_axis",
    )
)

# Show Y-axis selector configuration
SHOW_Y_AXIS_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=[SHOW_Y_AXIS_ON, SHOW_Y_AXIS_ON_WITH_TICK_MARKS, SHOW_Y_AXIS_OFF],
        mode=selector.SelectSelectorMode.DROPDOWN,
        translation_key="show_y_axis",
    )
)

# Label max selector configuration
LABEL_MAX_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=[LABEL_MAX_ON, LABEL_MAX_ON_NO_PRICE, LABEL_MAX_OFF],
        mode=selector.SelectSelectorMode.DROPDOWN,
        translation_key="label_max",
    )
)

# Label min selector configuration
LABEL_MIN_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=[LABEL_MIN_ON, LABEL_MIN_ON_NO_PRICE, LABEL_MIN_OFF],
        mode=selector.SelectSelectorMode.DROPDOWN,
        translation_key="label_min",
    )
)

# Cheap periods on X-axis selector configuration
CHEAP_PERIODS_ON_X_AXIS_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=[CHEAP_PERIODS_ON_X_AXIS_ON, CHEAP_PERIODS_ON_X_AXIS_ON_COMFY, CHEAP_PERIODS_ON_X_AXIS_ON_COMPACT, CHEAP_PERIODS_ON_X_AXIS_OFF],
        mode=selector.SelectSelectorMode.DROPDOWN,
        translation_key="cheap_periods_on_x_axis",
    )
)

# Refresh mode selector configuration
REFRESH_MODE_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=[REFRESH_MODE_SYSTEM, REFRESH_MODE_SYSTEM_INTERVAL, REFRESH_MODE_INTERVAL, REFRESH_MODE_MANUAL],
        mode=selector.SelectSelectorMode.DROPDOWN,
        translation_key="refresh_mode",
    )
)


class TibberGraphConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tibber Graph."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            price_entity_id = user_input.get(CONF_PRICE_ENTITY_ID)
            # Strip if it's a string, otherwise keep as None
            if isinstance(price_entity_id, str):
                price_entity_id = price_entity_id.strip() or None

            # Validate that either a price entity is provided or Tibber integration is configured
            if price_entity_id:
                # Validate the entity using helper function
                is_valid, error_key = validate_sensor_entity(self.hass, price_entity_id)
                if not is_valid:
                    errors["price_entity_id"] = error_key

                # Store the entity_id for later use
                user_input[CONF_PRICE_ENTITY_ID] = price_entity_id
            else:
                # No entity provided, check if Tibber integration is available
                if "tibber" not in self.hass.config.components:
                    errors["base"] = "no_price_source"

                # Clear entity_id if it was empty
                user_input[CONF_PRICE_ENTITY_ID] = None

            if not errors:
                # Generate a unique entity name if not provided
                entity_name = user_input.get(CONF_ENTITY_NAME, "").strip()
                if not entity_name:
                    if price_entity_id:
                        # Use the friendly name of the price entity
                        state = self.hass.states.get(price_entity_id)
                        if state and state.attributes.get("friendly_name"):
                            entity_name = state.attributes["friendly_name"]
                        else:
                            entity_name = price_entity_id.split(".")[-1].replace("_", " ").title()
                    else:
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
                    vol.Optional(CONF_PRICE_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Optional(CONF_ENTITY_NAME, default=""): cv.string,
                    vol.Optional(CONF_THEME, default=DEFAULT_THEME): THEME_SELECTOR,
                    vol.Optional(CONF_START_GRAPH_AT, default=DEFAULT_START_GRAPH_AT): START_GRAPH_AT_SELECTOR,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of nullable fields."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        entity_name = entry.data.get(CONF_ENTITY_NAME, DEFAULT_ENTITY_NAME)

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
                options=updated_options,
            )

        # Show form with checkboxes for resetting fields
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._get_reconfigure_schema(),
            description_placeholders={"entity_name": entity_name},
        )

    def _get_reconfigure_schema(self) -> vol.Schema:
        """Return schema for reconfiguring nullable fields."""
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
        entity_name = self.config_entry.data.get(CONF_ENTITY_NAME, DEFAULT_ENTITY_NAME)

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
            description_placeholders={"entity_name": entity_name},
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
                ): THEME_SELECTOR,
                vol.Optional(
                    CONF_TRANSPARENT_BACKGROUND,
                    default=options.get(CONF_TRANSPARENT_BACKGROUND, DEFAULT_TRANSPARENT_BACKGROUND),
                ): cv.boolean,
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
                vol.Optional(
                    CONF_LABEL_FONT_SIZE,
                    default=options.get(CONF_LABEL_FONT_SIZE, DEFAULT_LABEL_FONT_SIZE),
                ): cv.positive_int,
                vol.Optional(
                    CONF_START_GRAPH_AT,
                    default=options.get(CONF_START_GRAPH_AT, data.get(CONF_START_GRAPH_AT, DEFAULT_START_GRAPH_AT)),
                ): START_GRAPH_AT_SELECTOR,
                vol.Optional(
                    CONF_HOURS_TO_SHOW,
                    default=options.get(CONF_HOURS_TO_SHOW, DEFAULT_HOURS_TO_SHOW),
                ): vol.Any(None, cv.positive_int),
                vol.Optional(
                    CONF_CHEAP_PRICE_POINTS,
                    default=options.get(CONF_CHEAP_PRICE_POINTS, DEFAULT_CHEAP_PRICE_POINTS),
                ): cv.positive_int,
                vol.Optional(
                    CONF_CHEAP_PRICE_THRESHOLD,
                    default=options.get(CONF_CHEAP_PRICE_THRESHOLD, DEFAULT_CHEAP_PRICE_THRESHOLD),
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_SHOW_AVERAGE_PRICE_LINE,
                    default=options.get(CONF_SHOW_AVERAGE_PRICE_LINE, DEFAULT_SHOW_AVERAGE_PRICE_LINE),
                ): cv.boolean,
                vol.Optional(
                    CONF_COLOR_PRICE_LINE_BY_AVERAGE,
                    default=options.get(CONF_COLOR_PRICE_LINE_BY_AVERAGE, DEFAULT_COLOR_PRICE_LINE_BY_AVERAGE),
                ): cv.boolean,
                # Price labels
                vol.Optional(
                    CONF_PRICE_DECIMALS,
                    default=options.get(CONF_PRICE_DECIMALS, DEFAULT_PRICE_DECIMALS),
                ): vol.Any(None, cv.positive_int),
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
                    CONF_LABEL_SHOW_CURRENCY,
                    default=options.get(CONF_LABEL_SHOW_CURRENCY, DEFAULT_LABEL_SHOW_CURRENCY),
                ): cv.boolean,
                vol.Optional(
                    CONF_LABEL_CURRENT,
                    default=options.get(CONF_LABEL_CURRENT, DEFAULT_LABEL_CURRENT),
                ): LABEL_CURRENT_SELECTOR,
                vol.Optional(
                    CONF_LABEL_MIN,
                    default=options.get(CONF_LABEL_MIN, DEFAULT_LABEL_MIN),
                ): LABEL_MIN_SELECTOR,
                vol.Optional(
                    CONF_LABEL_MAX,
                    default=options.get(CONF_LABEL_MAX, DEFAULT_LABEL_MAX),
                ): LABEL_MAX_SELECTOR,
                vol.Optional(
                    CONF_LABEL_USE_COLORS,
                    default=options.get(CONF_LABEL_USE_COLORS, DEFAULT_LABEL_USE_COLORS),
                ): cv.boolean,
                # X-axis settings
                vol.Optional(
                    CONF_SHOW_X_AXIS,
                    default=options.get(CONF_SHOW_X_AXIS, DEFAULT_SHOW_X_AXIS),
                ): SHOW_X_AXIS_SELECTOR,
                vol.Optional(
                    CONF_X_TICK_STEP_HOURS,
                    default=options.get(CONF_X_TICK_STEP_HOURS, DEFAULT_X_TICK_STEP_HOURS),
                ): cv.positive_int,
                vol.Optional(
                    CONF_CHEAP_PERIODS_ON_X_AXIS,
                    default=options.get(CONF_CHEAP_PERIODS_ON_X_AXIS, DEFAULT_CHEAP_PERIODS_ON_X_AXIS),
                ): CHEAP_PERIODS_ON_X_AXIS_SELECTOR,
                vol.Optional(
                    CONF_SHOW_VERTICAL_GRID,
                    default=options.get(CONF_SHOW_VERTICAL_GRID, DEFAULT_SHOW_VERTICAL_GRID),
                ): cv.boolean,
                # Y-axis settings
                vol.Optional(
                    CONF_SHOW_Y_AXIS,
                    default=options.get(CONF_SHOW_Y_AXIS, DEFAULT_SHOW_Y_AXIS),
                ): SHOW_Y_AXIS_SELECTOR,
                vol.Optional(
                    CONF_Y_TICK_COUNT,
                    default=options.get(CONF_Y_TICK_COUNT, DEFAULT_Y_TICK_COUNT),
                ): vol.Any(None, cv.positive_int),
                vol.Optional(
                    CONF_Y_AXIS_LABEL_ROTATION_DEG,
                    default=options.get(CONF_Y_AXIS_LABEL_ROTATION_DEG, DEFAULT_Y_AXIS_LABEL_ROTATION_DEG),
                ): cv.positive_int,
                vol.Optional(
                    CONF_Y_AXIS_SIDE,
                    default=options.get(CONF_Y_AXIS_SIDE, DEFAULT_Y_AXIS_SIDE),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["left", "right"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="y_axis_side",
                    )
                ),
                vol.Optional(
                    CONF_Y_TICK_USE_COLORS,
                    default=options.get(CONF_Y_TICK_USE_COLORS, DEFAULT_Y_TICK_USE_COLORS),
                ): cv.boolean,
                vol.Optional(
                    CONF_SHOW_HORIZONTAL_GRID,
                    default=options.get(CONF_SHOW_HORIZONTAL_GRID, DEFAULT_SHOW_HORIZONTAL_GRID),
                ): cv.boolean,
                # Refresh settings
                vol.Optional(
                    CONF_REFRESH_MODE,
                    default=options.get(CONF_REFRESH_MODE, DEFAULT_REFRESH_MODE),
                ): REFRESH_MODE_SELECTOR,
            }
        )
