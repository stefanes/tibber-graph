"""Service handlers for Tibber Graph integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, entity_registry as er

from .themes import get_theme_names, validate_custom_theme
from .const import (
    DOMAIN,
    # Config entry keys
    CONF_PRICE_ENTITY_ID,
    # General config keys
    CONF_THEME,
    CONF_CUSTOM_THEME,
    CONF_TRANSPARENT_BACKGROUND,
    CONF_CANVAS_WIDTH,
    CONF_CANVAS_HEIGHT,
    CONF_FORCE_FIXED_SIZE,
    # X-axis config keys
    CONF_SHOW_X_TICKS,
    CONF_CHEAP_PRICE_ON_X_AXIS,
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
)

_LOGGER = logging.getLogger(__name__)

# Service names
SERVICE_SET_OPTION = "set_option"
SERVICE_RESET_OPTION = "reset_option"
SERVICE_SET_DATA_SOURCE = "set_data_source"
SERVICE_RENDER = "render"
SERVICE_SET_CUSTOM_THEME = "set_custom_theme"

# Service schema for set_option
SERVICE_SET_OPTION_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("options"): dict,
        vol.Optional("overwrite", default=False): cv.boolean,
    }
)

# Service schema for reset_option
SERVICE_RESET_OPTION_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("options", default=[]): vol.Any(list, None),
    }
)

# Service schema for set_data_source
SERVICE_SET_DATA_SOURCE_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("price_entity_id"): vol.Any(None, cv.entity_id),
    }
)

# Service schema for render
SERVICE_RENDER_SCHEMA = vol.Schema(
    {
        vol.Optional("entity_id"): cv.entity_ids,
    }
)

# Service schema for set_custom_theme
SERVICE_SET_CUSTOM_THEME_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("theme_config"): vol.Any(None, dict),
    }
)

# Valid option keys and their validators - theme options loaded dynamically
VALID_OPTIONS = {
    # General settings
    CONF_THEME: vol.In(get_theme_names()),
    CONF_TRANSPARENT_BACKGROUND: cv.boolean,
    CONF_CANVAS_WIDTH: cv.positive_int,
    CONF_CANVAS_HEIGHT: cv.positive_int,
    CONF_FORCE_FIXED_SIZE: cv.boolean,
    # X-axis settings
    CONF_SHOW_X_TICKS: cv.boolean,
    CONF_CHEAP_PRICE_ON_X_AXIS: cv.boolean,
    CONF_START_GRAPH_AT: vol.In([START_GRAPH_AT_MIDNIGHT, START_GRAPH_AT_CURRENT_HOUR, START_GRAPH_AT_SHOW_ALL]),
    CONF_X_TICK_STEP_HOURS: cv.positive_int,
    CONF_HOURS_TO_SHOW: vol.Any(None, cv.positive_int),
    CONF_SHOW_VERTICAL_GRID: cv.boolean,
    # Y-axis settings
    CONF_SHOW_Y_AXIS: cv.boolean,
    CONF_SHOW_Y_AXIS_TICKS: cv.boolean,
    CONF_SHOW_HORIZONTAL_GRID: cv.boolean,
    CONF_SHOW_AVERAGE_PRICE_LINE: cv.boolean,
    CONF_CHEAP_PRICE_POINTS: cv.positive_int,
    CONF_CHEAP_PRICE_THRESHOLD: vol.Coerce(float),
    CONF_Y_AXIS_LABEL_ROTATION_DEG: cv.positive_int,
    CONF_Y_AXIS_SIDE: vol.In(["left", "right"]),
    CONF_Y_TICK_COUNT: vol.Any(None, cv.positive_int),
    CONF_Y_TICK_USE_COLORS: cv.boolean,
    # Price label settings
    CONF_USE_HOURLY_PRICES: cv.boolean,
    CONF_USE_CENTS: cv.boolean,
    CONF_CURRENCY_OVERRIDE: vol.Any(None, str),
    CONF_LABEL_CURRENT: cv.boolean,
    CONF_LABEL_CURRENT_IN_HEADER: cv.boolean,
    CONF_LABEL_CURRENT_IN_HEADER_MORE: cv.boolean,
    CONF_LABEL_FONT_SIZE: cv.positive_int,
    CONF_LABEL_MAX: cv.boolean,
    CONF_LABEL_MIN: cv.boolean,
    CONF_LABEL_MINMAX_SHOW_PRICE: cv.boolean,
    CONF_LABEL_SHOW_CURRENCY: cv.boolean,
    CONF_LABEL_USE_COLORS: cv.boolean,
    CONF_PRICE_DECIMALS: vol.Any(None, cv.positive_int),
    CONF_COLOR_PRICE_LINE_BY_AVERAGE: cv.boolean,
    # Refresh settings
    CONF_AUTO_REFRESH_ENABLED: cv.boolean,
}


async def async_register_services(hass: HomeAssistant) -> None:
    """Register services for Tibber Graph integration."""
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_OPTION,
        async_handle_set_option,
        schema=SERVICE_SET_OPTION_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_OPTION,
        async_handle_reset_option,
        schema=SERVICE_RESET_OPTION_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_DATA_SOURCE,
        async_handle_set_data_source,
        schema=SERVICE_SET_DATA_SOURCE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RENDER,
        async_handle_render,
        schema=SERVICE_RENDER_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CUSTOM_THEME,
        async_handle_set_custom_theme,
        schema=SERVICE_SET_CUSTOM_THEME_SCHEMA,
    )


async def async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister services for Tibber Graph integration."""
    hass.services.async_remove(DOMAIN, SERVICE_SET_OPTION)
    hass.services.async_remove(DOMAIN, SERVICE_RESET_OPTION)
    hass.services.async_remove(DOMAIN, SERVICE_SET_DATA_SOURCE)
    hass.services.async_remove(DOMAIN, SERVICE_RENDER)
    hass.services.async_remove(DOMAIN, SERVICE_SET_CUSTOM_THEME)


async def async_handle_set_option(call: ServiceCall) -> None:
    """Handle set_option service call."""
    hass = call.hass
    entity_id = call.data["entity_id"]
    options = call.data["options"]
    overwrite = call.data.get("overwrite", False)

    # Get the config entry for this entity
    config_entry = await _get_config_entry_for_entity(hass, entity_id)
    if not config_entry:
        raise HomeAssistantError(f"Entity {entity_id} not found or is not a Tibber Graph entity")

    # Validate and sanitize options
    validated_options = {}
    for key, value in options.items():
        if key not in VALID_OPTIONS:
            raise HomeAssistantError(f"Invalid option: {key}")

        # Clean string values
        if isinstance(value, str):
            value = value.strip()
            # Convert empty strings to None for nullable fields
            if value == "" and key in [CONF_HOURS_TO_SHOW, CONF_Y_TICK_COUNT, CONF_PRICE_DECIMALS, CONF_CURRENCY_OVERRIDE]:
                value = None

        # Validate the value
        try:
            validated_value = VALID_OPTIONS[key](value)
            validated_options[key] = validated_value
        except (vol.Invalid, ValueError) as err:
            raise HomeAssistantError(f"Invalid value for {key}: {value}. Error: {err}") from err

    # Determine new options based on overwrite flag
    if overwrite:
        # When overwrite is True, start with only the provided options
        # All unprovided options will revert to defaults (by not being in config entry options)
        new_options = validated_options
        _LOGGER.info("Updated options for %s (overwrite=True): %s", entity_id, validated_options)
    else:
        # When overwrite is False, merge with existing options (default behavior)
        new_options = {**config_entry.options, **validated_options}
        _LOGGER.info("Updated options for %s: %s", entity_id, validated_options)

    # Update the config entry options
    hass.config_entries.async_update_entry(config_entry, options=new_options)
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_handle_reset_option(call: ServiceCall) -> None:
    """Handle reset_option service call."""
    hass = call.hass
    entity_id = call.data["entity_id"]
    options_to_reset = call.data.get("options", [])

    # Get the config entry for this entity
    config_entry = await _get_config_entry_for_entity(hass, entity_id)
    if not config_entry:
        raise HomeAssistantError(f"Entity {entity_id} not found or is not a Tibber Graph entity")

    # If options list is empty or None, reset all options
    if not options_to_reset:
        new_options = {}
        _LOGGER.info("Reset all options for %s", entity_id)
    else:
        # Validate option names
        for option in options_to_reset:
            if option not in VALID_OPTIONS:
                raise HomeAssistantError(f"Invalid option: {option}")

        # Remove specified options from config entry
        new_options = {k: v for k, v in config_entry.options.items() if k not in options_to_reset}
        _LOGGER.info("Reset options for %s: %s", entity_id, options_to_reset)

    # Update the config entry
    hass.config_entries.async_update_entry(config_entry, options=new_options)
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_handle_render(call: ServiceCall) -> None:
    """Handle render service call."""
    hass = call.hass
    entity_ids = call.data.get("entity_id")

    # Get the entity registry
    entity_registry = er.async_get(hass)

    # If no entity_id provided, render all Tibber Graph entities
    if not entity_ids:
        all_entities = er.async_entries_for_domain(entity_registry, DOMAIN)
        entity_ids = [entry.entity_id for entry in all_entities]
        if not entity_ids:
            raise HomeAssistantError("No Tibber Graph entities found")
        _LOGGER.info("Rendering all Tibber Graph entities: %s", entity_ids)
    elif isinstance(entity_ids, str):
        entity_ids = [entity_ids]

    # Get the entity component
    entity_comp = hass.data.get("entity_components", {}).get("camera")
    if not entity_comp:
        raise HomeAssistantError("Camera component not loaded")

    # Render each entity
    rendered_count = 0
    for entity_id in entity_ids:
        # Validate entity belongs to this integration
        entity_entry = entity_registry.async_get(entity_id)
        if not entity_entry or entity_entry.platform != DOMAIN:
            _LOGGER.warning("Skipping %s: not found or is not a Tibber Graph entity", entity_id)
            continue

        # Get the entity object and call render method
        entity_obj = entity_comp.get_entity(entity_id)
        if entity_obj and hasattr(entity_obj, "async_render_image"):
            await entity_obj.async_render_image(triggered_by="action")
            rendered_count += 1
            _LOGGER.info("Triggered render for %s", entity_id)
        else:
            _LOGGER.warning("Skipping %s: does not support rendering", entity_id)

    if rendered_count == 0:
        raise HomeAssistantError("No valid Tibber Graph entities were rendered")

    _LOGGER.info("Successfully rendered %d Tibber Graph entit%s", rendered_count, "y" if rendered_count == 1 else "ies")


async def async_handle_set_data_source(call: ServiceCall) -> None:
    """Handle set_data_source service call."""
    hass = call.hass
    entity_id = call.data["entity_id"]
    price_entity_id = call.data.get("price_entity_id")

    # Strip if it's a string, otherwise keep as None
    if isinstance(price_entity_id, str):
        price_entity_id = price_entity_id.strip() or None

    # Get the config entry for this entity
    config_entry = await _get_config_entry_for_entity(hass, entity_id)
    if not config_entry:
        raise HomeAssistantError(f"Entity {entity_id} not found or is not a Tibber Graph entity")

    # Validate the new data source
    if price_entity_id:
        # Validate the entity exists and is a sensor
        entity_registry = er.async_get(hass)
        entity_entry = entity_registry.async_get(price_entity_id)

        if not entity_entry:
            # Try to get the state to check if entity exists
            state = hass.states.get(price_entity_id)
            if not state:
                raise HomeAssistantError(f"Entity {price_entity_id} not found")
            elif not price_entity_id.startswith("sensor."):
                raise HomeAssistantError(f"Entity {price_entity_id} is not a sensor")
        elif entity_entry.domain != "sensor":
            raise HomeAssistantError(f"Entity {price_entity_id} is not a sensor")
    else:
        # No entity provided, check if Tibber integration is available
        if "tibber" not in hass.config.components:
            raise HomeAssistantError("Either a price entity must be provided or the Tibber integration must be configured")

    # Update entry data with new price entity ID
    updated_data = dict(config_entry.data)
    updated_data[CONF_PRICE_ENTITY_ID] = price_entity_id
    hass.config_entries.async_update_entry(config_entry, data=updated_data)
    await hass.config_entries.async_reload(config_entry.entry_id)

    source_name = price_entity_id if price_entity_id else "Tibber Integration"
    _LOGGER.info("Updated data source for %s to: %s", entity_id, source_name)


async def async_handle_set_custom_theme(call: ServiceCall) -> None:
    """Handle set_custom_theme service call."""
    hass = call.hass
    entity_id = call.data["entity_id"]
    theme_config = call.data.get("theme_config")

    # Get the config entry for this entity
    config_entry = await _get_config_entry_for_entity(hass, entity_id)
    if not config_entry:
        raise HomeAssistantError(f"Entity {entity_id} not found or is not a Tibber Graph entity")

    # If theme_config is None or empty dict, clear the custom theme
    if not theme_config:
        new_options = {k: v for k, v in config_entry.options.items() if k != CONF_CUSTOM_THEME}
        hass.config_entries.async_update_entry(config_entry, options=new_options)
        await hass.config_entries.async_reload(config_entry.entry_id)
        _LOGGER.info("Cleared custom theme for %s, reverted to configured theme", entity_id)
        return

    # Validate the custom theme
    is_valid, error_message = validate_custom_theme(theme_config)
    if not is_valid:
        raise HomeAssistantError(f"Invalid custom theme: {error_message}")

    # Store the custom theme in config entry options
    new_options = {**config_entry.options, CONF_CUSTOM_THEME: theme_config}
    hass.config_entries.async_update_entry(config_entry, options=new_options)
    await hass.config_entries.async_reload(config_entry.entry_id)

    _LOGGER.info("Set custom theme for %s", entity_id)


async def _get_config_entry_for_entity(hass: HomeAssistant, entity_id: str) -> ConfigEntry | None:
    """Get the config entry for a given entity ID."""
    entity_registry = er.async_get(hass)
    entity_entry = entity_registry.async_get(entity_id)

    if not entity_entry:
        return None

    # Check if the entity belongs to this integration
    if entity_entry.platform != DOMAIN:
        return None

    # Get the config entry
    config_entry = hass.config_entries.async_get_entry(entity_entry.config_entry_id)
    return config_entry
