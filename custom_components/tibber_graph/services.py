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
from .helpers import get_config_entry_for_device_entity, validate_sensor_entity, get_entity_friendly_name
from .const import (
    DOMAIN,
    # Config entry keys
    CONF_ENTITY_NAME,
    CONF_PRICE_ENTITY_ID,
    # Custom data source config keys
    CONF_DATA_ATTR,
    CONF_DATA_ATTR_START_FIELD,
    CONF_DATA_ATTR_START_FMT,
    CONF_DATA_ATTR_PRICE_FIELD,
    CONF_DATA_ATTR_PRICE_FACTOR,
    CONF_DATA_ATTR_PRICE_ADD,
    CONF_CURRENCY_ATTR,
    # General config keys
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
    CONF_SHOW_CHEAP_PRICE_LINE,
    # Cheap periods on X-axis options
    CHEAP_PERIODS_ON_X_AXIS_ON,
    CHEAP_PERIODS_ON_X_AXIS_ON_COMFY,
    CHEAP_PERIODS_ON_X_AXIS_ON_COMPACT,
    CHEAP_PERIODS_ON_X_AXIS_OFF,
    # Cheap boundary highlight options
    CHEAP_BOUNDARY_HIGHLIGHT_NONE,
    CHEAP_BOUNDARY_HIGHLIGHT_UNDERLINE,
    CHEAP_BOUNDARY_HIGHLIGHT_UNDERLINE_ALL,
    # Y-axis config keys
    CONF_SHOW_Y_AXIS,
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
    CONF_LABEL_FONT_SIZE,
    CONF_LABEL_MAX,
    CONF_LABEL_MIN,
    CONF_LABEL_SHOW_CURRENCY,
    CONF_LABEL_USE_COLORS,
    CONF_LABEL_MINMAX_PER_DAY,
    CONF_PRICE_DECIMALS,
    CONF_COLOR_PRICE_LINE_BY_AVERAGE,
    # Refresh config keys
    CONF_REFRESH_MODE,
    # Footer config keys
    CONF_SHOW_DATA_SOURCE_NAME,
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
    # Y-axis side options
    Y_AXIS_SIDE_LEFT,
    Y_AXIS_SIDE_RIGHT,
    # Refresh mode options
    REFRESH_MODE_SYSTEM,
    REFRESH_MODE_SYSTEM_INTERVAL,
    REFRESH_MODE_INTERVAL,
    REFRESH_MODE_SENSOR,
    REFRESH_MODE_MANUAL,
    # External domain constants
    SENSOR_DOMAIN,
    TIBBER_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _clean_string_or_none(value: Any) -> str | None:
    """Clean and validate string input, returning None for empty strings.

    Args:
        value: Input value to clean

    Returns:
        Cleaned string or None if empty/None
    """
    if isinstance(value, str):
        return value.strip() or None
    return None


def _validate_refresh_mode(refresh_mode: str, price_entity_id: str | None) -> str:
    """Validate refresh mode and fallback to system mode if sensor mode is invalid.

    Sensor refresh mode is only supported with custom data source entities.
    If sensor mode is requested without a price entity, fall back to system mode.

    Args:
        refresh_mode: The requested refresh mode
        price_entity_id: The price entity ID (None for Tibber integration)

    Returns:
        The validated refresh mode (possibly changed to REFRESH_MODE_SYSTEM)
    """
    if refresh_mode == REFRESH_MODE_SENSOR and not price_entity_id:
        _LOGGER.warning(
            "Sensor refresh mode is only supported with a price sensor as data source. "
            "Falling back to system mode."
        )
        return REFRESH_MODE_SYSTEM
    return refresh_mode


# Service names
SERVICE_SET_OPTION = "set_option"
SERVICE_RESET_OPTION = "reset_option"
SERVICE_SET_DATA_SOURCE = "set_data_source"
SERVICE_RENDER = "render"
SERVICE_SET_CUSTOM_THEME = "set_custom_theme"
SERVICE_CREATE_GRAPH = "create_graph"
SERVICE_DELETE_GRAPH = "delete_graph"
SERVICE_EXPORT_CONFIG = "export_config"

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
        vol.Optional("data_attr"): vol.Any(None, cv.string),
        vol.Optional("data_attr_start_field"): vol.Any(None, cv.string),
        vol.Optional("data_attr_start_fmt"): vol.Any(None, cv.string),
        vol.Optional("data_attr_price_field"): vol.Any(None, cv.string),
        vol.Optional("data_attr_price_factor"): vol.Any(None, vol.Coerce(float)),
        vol.Optional("data_attr_price_add"): vol.Any(None, vol.Coerce(float)),
        vol.Optional("currency_attr"): vol.Any(None, cv.string),
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

# Service schema for create_graph
SERVICE_CREATE_GRAPH_SCHEMA = vol.Schema(
    {
        vol.Optional("entity_name"): cv.string,
        vol.Optional("price_entity_id"): vol.Any(None, cv.entity_id),
        vol.Optional("options"): dict,
        vol.Optional("custom_theme"): dict,
        vol.Optional("recreate", default=False): cv.boolean,
        vol.Optional("data_attr"): vol.Any(None, cv.string),
        vol.Optional("data_attr_start_field"): vol.Any(None, cv.string),
        vol.Optional("data_attr_start_fmt"): vol.Any(None, cv.string),
        vol.Optional("data_attr_price_field"): vol.Any(None, cv.string),
        vol.Optional("data_attr_price_factor"): vol.Any(None, vol.Coerce(float)),
        vol.Optional("data_attr_price_add"): vol.Any(None, vol.Coerce(float)),
        vol.Optional("currency_attr"): vol.Any(None, cv.string),
    }
)

# Service schema for delete_graph
SERVICE_DELETE_GRAPH_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_ids,
    }
)

# Service schema for export_config
SERVICE_EXPORT_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
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
    CONF_SHOW_X_AXIS: vol.In([SHOW_X_AXIS_ON, SHOW_X_AXIS_ON_WITH_TICK_MARKS, SHOW_X_AXIS_OFF]),
    CONF_CHEAP_PERIODS_ON_X_AXIS: vol.In([CHEAP_PERIODS_ON_X_AXIS_ON, CHEAP_PERIODS_ON_X_AXIS_ON_COMFY, CHEAP_PERIODS_ON_X_AXIS_ON_COMPACT, CHEAP_PERIODS_ON_X_AXIS_OFF]),
    CONF_START_GRAPH_AT: vol.In([START_GRAPH_AT_MIDNIGHT, START_GRAPH_AT_CURRENT_HOUR, START_GRAPH_AT_SHOW_ALL]),
    CONF_X_TICK_STEP_HOURS: cv.positive_int,
    CONF_HOURS_TO_SHOW: vol.Any(None, cv.positive_int),
    CONF_SHOW_VERTICAL_GRID: cv.boolean,
    CONF_CHEAP_BOUNDARY_HIGHLIGHT: vol.In([CHEAP_BOUNDARY_HIGHLIGHT_NONE, CHEAP_BOUNDARY_HIGHLIGHT_UNDERLINE, CHEAP_BOUNDARY_HIGHLIGHT_UNDERLINE_ALL]),
    # Y-axis settings
    CONF_SHOW_Y_AXIS: vol.In([SHOW_Y_AXIS_ON, SHOW_Y_AXIS_ON_WITH_TICK_MARKS, SHOW_Y_AXIS_OFF]),
    CONF_SHOW_HORIZONTAL_GRID: cv.boolean,
    CONF_SHOW_AVERAGE_PRICE_LINE: cv.boolean,
    CONF_CHEAP_PRICE_POINTS: cv.positive_int,
    CONF_CHEAP_PRICE_THRESHOLD: vol.Coerce(float),
    CONF_Y_AXIS_LABEL_ROTATION_DEG: cv.positive_int,
    CONF_Y_AXIS_SIDE: vol.In([Y_AXIS_SIDE_LEFT, Y_AXIS_SIDE_RIGHT]),
    CONF_Y_TICK_COUNT: vol.Any(None, cv.positive_int),
    CONF_Y_TICK_USE_COLORS: cv.boolean,
    # Price label settings
    CONF_USE_HOURLY_PRICES: cv.boolean,
    CONF_USE_CENTS: cv.boolean,
    CONF_CURRENCY_OVERRIDE: vol.Any(None, str),
    CONF_LABEL_CURRENT: vol.In([LABEL_CURRENT_ON, LABEL_CURRENT_ON_CURRENT_PRICE_ONLY, LABEL_CURRENT_ON_IN_GRAPH, LABEL_CURRENT_ON_IN_GRAPH_NO_PRICE, LABEL_CURRENT_OFF]),
    CONF_LABEL_FONT_SIZE: cv.positive_int,
    CONF_LABEL_MAX: vol.In([LABEL_MAX_ON, LABEL_MAX_ON_NO_PRICE, LABEL_MAX_OFF]),
    CONF_LABEL_MIN: vol.In([LABEL_MIN_ON, LABEL_MIN_ON_NO_PRICE, LABEL_MIN_OFF]),
    CONF_LABEL_SHOW_CURRENCY: cv.boolean,
    CONF_LABEL_USE_COLORS: cv.boolean,
    CONF_LABEL_MINMAX_PER_DAY: cv.boolean,
    CONF_PRICE_DECIMALS: vol.Any(None, cv.positive_int),
    CONF_COLOR_PRICE_LINE_BY_AVERAGE: cv.boolean,
    CONF_SHOW_CHEAP_PRICE_LINE: cv.boolean,
    # Refresh settings
    CONF_REFRESH_MODE: vol.In([REFRESH_MODE_SYSTEM, REFRESH_MODE_SYSTEM_INTERVAL, REFRESH_MODE_INTERVAL, REFRESH_MODE_SENSOR, REFRESH_MODE_MANUAL]),
    # Footer settings
    CONF_SHOW_DATA_SOURCE_NAME: cv.boolean,
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

    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_GRAPH,
        async_handle_create_graph,
        schema=SERVICE_CREATE_GRAPH_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_GRAPH,
        async_handle_delete_graph,
        schema=SERVICE_DELETE_GRAPH_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_CONFIG,
        async_handle_export_config,
        schema=SERVICE_EXPORT_CONFIG_SCHEMA,
        supports_response="only",
    )


async def async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister services for Tibber Graph integration."""
    hass.services.async_remove(DOMAIN, SERVICE_SET_OPTION)
    hass.services.async_remove(DOMAIN, SERVICE_RESET_OPTION)
    hass.services.async_remove(DOMAIN, SERVICE_SET_DATA_SOURCE)
    hass.services.async_remove(DOMAIN, SERVICE_RENDER)
    hass.services.async_remove(DOMAIN, SERVICE_SET_CUSTOM_THEME)
    hass.services.async_remove(DOMAIN, SERVICE_CREATE_GRAPH)
    hass.services.async_remove(DOMAIN, SERVICE_DELETE_GRAPH)
    hass.services.async_remove(DOMAIN, SERVICE_EXPORT_CONFIG)


async def async_handle_set_option(call: ServiceCall) -> None:
    """Handle set_option service call."""
    hass = call.hass
    entity_id = call.data["entity_id"]
    options = call.data["options"]
    overwrite = call.data.get("overwrite", False)

    # Get the config entry for this entity (works with camera, image, or sensor)
    config_entry = await get_config_entry_for_device_entity(hass, entity_id, DOMAIN)
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

    # Special validation for refresh_mode: sensor mode requires custom data source
    if CONF_REFRESH_MODE in validated_options:
        refresh_mode = validated_options[CONF_REFRESH_MODE]
        price_entity_id = config_entry.data.get(CONF_PRICE_ENTITY_ID)
        validated_options[CONF_REFRESH_MODE] = _validate_refresh_mode(refresh_mode, price_entity_id)

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

    # Get the config entry for this entity (works with camera, image, or sensor)
    config_entry = await get_config_entry_for_device_entity(hass, entity_id, DOMAIN)
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

    # If no entity_id provided, render all Tibber Graph camera entities
    if not entity_ids:
        # Filter for camera entities that belong to tibber_graph platform
        all_entities = [
            entry for entry in entity_registry.entities.values()
            if entry.platform == DOMAIN and entry.domain == "camera"
        ]
        entity_ids = [entry.entity_id for entry in all_entities]
        if not entity_ids:
            raise HomeAssistantError("No Tibber Graph entities found")
        _LOGGER.info("Rendering all Tibber Graph camera entities: %s", entity_ids)
    elif isinstance(entity_ids, str):
        entity_ids = [entity_ids]

    # Get the entity component
    entity_comp = hass.data.get("entity_components", {}).get("camera")
    if not entity_comp:
        raise HomeAssistantError("Camera component not loaded")

    # Render each entity (resolve to camera if needed)
    rendered_count = 0
    for entity_id in entity_ids:
        # Get the config entry for this entity (works with camera, image, or sensor)
        config_entry = await get_config_entry_for_device_entity(hass, entity_id, DOMAIN)
        if not config_entry:
            _LOGGER.warning("Skipping %s: not found or is not a Tibber Graph entity", entity_id)
            continue

        # Find the camera entity for this device
        camera_entity_id = None
        for entry in entity_registry.entities.values():
            if (entry.config_entry_id == config_entry.entry_id and
                entry.platform == DOMAIN and
                entry.domain == "camera"):
                camera_entity_id = entry.entity_id
                break

        if not camera_entity_id:
            _LOGGER.warning("Skipping %s: no camera entity found for this device", entity_id)
            continue

        # Get the camera entity object and call render method
        camera_obj = entity_comp.get_entity(camera_entity_id)
        if camera_obj and hasattr(camera_obj, "async_render_image"):
            await camera_obj.async_render_image(triggered_by="action")
            rendered_count += 1
            _LOGGER.info("Triggered render for %s via %s", camera_entity_id, entity_id)
        else:
            _LOGGER.warning("Skipping %s: camera entity does not support rendering", camera_entity_id)

    if rendered_count == 0:
        raise HomeAssistantError("No valid Tibber Graph entities were rendered")

    _LOGGER.info("Successfully rendered %d Tibber Graph entit%s", rendered_count, "y" if rendered_count == 1 else "ies")


async def async_handle_set_data_source(call: ServiceCall) -> None:
    """Handle set_data_source service call."""
    hass = call.hass
    entity_id = call.data["entity_id"]
    price_entity_id = _clean_string_or_none(call.data.get("price_entity_id"))

    # Get custom data source parameters
    data_attr = _clean_string_or_none(call.data.get("data_attr"))
    data_attr_price_field = _clean_string_or_none(call.data.get("data_attr_price_field"))
    data_attr_start_field = _clean_string_or_none(call.data.get("data_attr_start_field"))
    data_attr_start_fmt = _clean_string_or_none(call.data.get("data_attr_start_fmt"))
    data_attr_price_factor = call.data.get("data_attr_price_factor")
    data_attr_price_add = call.data.get("data_attr_price_add")
    currency_attr = _clean_string_or_none(call.data.get("currency_attr"))

    # Get the config entry for this entity (works with camera, image, or sensor)
    config_entry = await get_config_entry_for_device_entity(hass, entity_id, DOMAIN)
    if not config_entry:
        raise HomeAssistantError(f"Entity {entity_id} not found or is not a Tibber Graph entity")

    # Validate the new data source
    if price_entity_id:
        is_valid, error_key = validate_sensor_entity(hass, price_entity_id)
        if not is_valid:
            if error_key == "entity_not_found":
                raise HomeAssistantError(f"Entity {price_entity_id} not found")
            else:
                raise HomeAssistantError(f"Entity {price_entity_id} is not a sensor")
    else:
        # No entity provided, check if Tibber integration is available
        if "tibber" not in hass.config.components:
            raise HomeAssistantError("Either a price entity must be provided or the Tibber integration must be configured")

    # Update entry data with new price entity ID and custom data source parameters
    updated_data = dict(config_entry.data)
    updated_data[CONF_PRICE_ENTITY_ID] = price_entity_id

    # Store custom data source parameters (None values will be stored to reset to defaults)
    updated_data[CONF_DATA_ATTR] = data_attr
    updated_data[CONF_DATA_ATTR_PRICE_FIELD] = data_attr_price_field
    updated_data[CONF_DATA_ATTR_START_FIELD] = data_attr_start_field
    updated_data[CONF_DATA_ATTR_START_FMT] = data_attr_start_fmt
    updated_data[CONF_DATA_ATTR_PRICE_FACTOR] = data_attr_price_factor
    updated_data[CONF_DATA_ATTR_PRICE_ADD] = data_attr_price_add
    updated_data[CONF_CURRENCY_ATTR] = currency_attr

    hass.config_entries.async_update_entry(config_entry, data=updated_data)
    await hass.config_entries.async_reload(config_entry.entry_id)

    source_name = price_entity_id if price_entity_id else "Tibber Integration"
    _LOGGER.info("Updated data source for %s to: %s", entity_id, source_name)


async def async_handle_set_custom_theme(call: ServiceCall) -> None:
    """Handle set_custom_theme service call."""
    hass = call.hass
    entity_id = call.data["entity_id"]
    theme_config = call.data.get("theme_config")

    # Get the config entry for this entity (works with camera, image, or sensor)
    config_entry = await get_config_entry_for_device_entity(hass, entity_id, DOMAIN)
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


async def async_handle_create_graph(call: ServiceCall) -> dict[str, str]:
    """Handle create_graph service call."""
    hass = call.hass
    entity_name = _clean_string_or_none(call.data.get("entity_name")) or ""
    price_entity_id = _clean_string_or_none(call.data.get("price_entity_id"))
    options = call.data.get("options", {})
    custom_theme = call.data.get("custom_theme")
    recreate = call.data.get("recreate", False)

    # Get custom data source parameters
    data_attr = _clean_string_or_none(call.data.get("data_attr"))
    data_attr_price_field = _clean_string_or_none(call.data.get("data_attr_price_field"))
    data_attr_start_field = _clean_string_or_none(call.data.get("data_attr_start_field"))
    data_attr_start_fmt = _clean_string_or_none(call.data.get("data_attr_start_fmt"))
    data_attr_price_factor = call.data.get("data_attr_price_factor")
    data_attr_price_add = call.data.get("data_attr_price_add")
    currency_attr = _clean_string_or_none(call.data.get("currency_attr"))

    # Validate price entity if provided
    if price_entity_id:
        is_valid, error_key = validate_sensor_entity(hass, price_entity_id)
        if not is_valid:
            if error_key == "entity_not_found":
                raise HomeAssistantError(f"Entity {price_entity_id} not found")
            else:
                raise HomeAssistantError(f"Entity {price_entity_id} is not a sensor")
    else:
        # No entity provided, check if Tibber integration is available
        if TIBBER_DOMAIN not in hass.config.components:
            raise HomeAssistantError("Either a price entity must be provided or the Tibber integration must be configured")

    # Generate entity name if not provided (same logic as config_flow)
    if not entity_name:
        if price_entity_id:
            # Use the friendly name of the price entity
            entity_name = get_entity_friendly_name(hass, price_entity_id)
        else:
            # Auto-generate entity name based on Tibber home
            try:
                homes = hass.data["tibber"].get_homes(only_active=True)
                if homes:
                    home = homes[0]
                    if not home.info:
                        await home.update_info()
                    entity_name = home.info['viewer']['home']['appNickname'] or home.info['viewer']['home']['address'].get('address1', 'Tibber Graph')
            except Exception:
                entity_name = "Tibber Graph"

    # Check if entity with this name already exists
    existing_entries = hass.config_entries.async_entries(DOMAIN)
    existing_entry = None
    for entry in existing_entries:
        if entry.data.get(CONF_ENTITY_NAME, "").lower() == entity_name.lower():
            existing_entry = entry
            break

    if existing_entry:
        if not recreate:
            raise HomeAssistantError(f"Entity with name '{entity_name}' already exists. Set recreate=true to replace it.")

        # Remove existing entry
        _LOGGER.info("Recreating existing entity: %s", entity_name)
        await hass.config_entries.async_remove(existing_entry.entry_id)

    # Validate options if provided
    validated_options = {}
    if options:
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
                raise HomeAssistantError(f"Invalid value for option '{key}': {value}. Error: {err}") from err

        # Special validation for refresh_mode: sensor mode requires a price sensor as data source
        if CONF_REFRESH_MODE in validated_options:
            validated_options[CONF_REFRESH_MODE] = _validate_refresh_mode(
                validated_options[CONF_REFRESH_MODE],
                price_entity_id
            )

    # Validate custom theme if provided
    if custom_theme:
        is_valid, error_message = validate_custom_theme(custom_theme)
        if not is_valid:
            raise HomeAssistantError(f"Invalid custom theme: {error_message}")
        # Add custom theme to options
        validated_options[CONF_CUSTOM_THEME] = custom_theme

    # Create config entry data
    entry_data = {
        CONF_ENTITY_NAME: entity_name,
        CONF_PRICE_ENTITY_ID: price_entity_id,
        # Store custom data source parameters
        CONF_DATA_ATTR: data_attr,
        CONF_DATA_ATTR_PRICE_FIELD: data_attr_price_field,
        CONF_DATA_ATTR_START_FIELD: data_attr_start_field,
        CONF_DATA_ATTR_START_FMT: data_attr_start_fmt,
        CONF_DATA_ATTR_PRICE_FACTOR: data_attr_price_factor,
        CONF_DATA_ATTR_PRICE_ADD: data_attr_price_add,
        CONF_CURRENCY_ATTR: currency_attr,
    }

    # Create the config entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
        data=entry_data,
    )

    if result["type"] != "create_entry":
        raise HomeAssistantError(f"Failed to create entity: {result.get('reason', 'Unknown error')}")

    # Get the newly created entry
    entry_id = result["result"].entry_id
    config_entry = hass.config_entries.async_get_entry(entry_id)

    if not config_entry:
        raise HomeAssistantError("Failed to retrieve created config entry")

    # Update options if provided
    if validated_options:
        hass.config_entries.async_update_entry(config_entry, options=validated_options)
        await hass.config_entries.async_reload(entry_id)

    # Generate the expected camera entity ID
    name_sanitized = entity_name.lower().replace(" ", "_").replace("-", "_")
    camera_entity_id = f"camera.tibber_graph_{name_sanitized}"

    _LOGGER.info("Successfully created Tibber Graph entity: %s (camera: %s)", entity_name, camera_entity_id)

    return {"entity_id": camera_entity_id}


async def async_handle_export_config(call: ServiceCall) -> dict[str, Any]:
    """Handle export_config service call."""
    from . import const

    hass = call.hass
    entity_id = call.data["entity_id"]

    # Get the config entry for this entity (works with camera, image, or sensor)
    config_entry = await get_config_entry_for_device_entity(hass, entity_id, DOMAIN)
    if not config_entry:
        raise HomeAssistantError(f"Entity {entity_id} not found or is not a Tibber Graph entity")

    # Build the export dictionary
    export_data: dict[str, Any] = {}

    # Collect options that differ from defaults
    options_dict = {}
    for key, value in config_entry.options.items():
        # Skip custom theme, it will be handled separately
        if key == CONF_CUSTOM_THEME:
            continue

        # Get the default value for this key
        default_key = f"DEFAULT_{key.upper()}"
        default_value = getattr(const, default_key, None)

        # Only include if different from default
        if value != default_value:
            options_dict[key] = value

    # Add options to export if any exist
    if options_dict:
        export_data["options"] = options_dict

    # Add custom theme if present
    custom_theme = config_entry.options.get(CONF_CUSTOM_THEME)
    if custom_theme:
        export_data["custom_theme"] = custom_theme

    _LOGGER.info("Exported configuration for %s", entity_id)

    return export_data


async def async_handle_delete_graph(call: ServiceCall) -> None:
    """Handle delete_graph service call."""
    hass = call.hass
    entity_ids = call.data.get("entity_id")

    # Convert single entity ID to list
    if isinstance(entity_ids, str):
        entity_ids = [entity_ids]

    # Process each entity
    for entity_id in entity_ids:
        try:
            # Get the config entry for this entity (works with camera, image, or sensor)
            config_entry = await get_config_entry_for_device_entity(hass, entity_id, DOMAIN)
            if not config_entry:
                _LOGGER.warning("Skipping %s: not found or is not a Tibber Graph entity", entity_id)
                continue

            # Get entity name for logging
            entity_name = config_entry.data.get(CONF_ENTITY_NAME, "Unknown")

            # Remove the config entry
            _LOGGER.info("Deleting Tibber Graph entity: %s (camera: %s)", entity_name, entity_id)
            await hass.config_entries.async_remove(config_entry.entry_id)

            _LOGGER.info("Successfully deleted Tibber Graph entity: %s", entity_id)

        except Exception as err:
            _LOGGER.error("Failed to delete entity %s: %s", entity_id, err)
