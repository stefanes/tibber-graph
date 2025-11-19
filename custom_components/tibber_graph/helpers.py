"""Helper functions for Tibber Graph component."""
from __future__ import annotations

import datetime
from dateutil import tz

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

# Reuse local timezone object
LOCAL_TZ = tz.tzlocal()


def ensure_timezone(dt: datetime.datetime, tz_info=None) -> datetime.datetime:
    """Ensure a datetime object has timezone information.

    Args:
        dt: datetime object to check
        tz_info: timezone to apply if missing (defaults to LOCAL_TZ)

    Returns:
        datetime object with timezone information
    """
    if tz_info is None:
        tz_info = LOCAL_TZ
    # For Python 3.11+, use replace() for all timezone objects
    return dt if dt.tzinfo else dt.replace(tzinfo=tz_info)


def get_graph_file_path(hass, entity_name: str) -> str:
    """Generate the PNG file path for a Tibber Graph entity.

    Args:
        hass: Home Assistant instance
        entity_name: The entity name from the config entry

    Returns:
        str: Absolute path to the PNG file
    """
    name_sanitized = entity_name.lower().replace(" ", "_").replace("-", "_")
    return hass.config.path(f"www/tibber_graph_{name_sanitized}.png")


def get_unique_id(entity_type: str, entity_name: str, entry_id: str) -> str:
    """Generate a unique ID for a Tibber Graph entity.

    Args:
        entity_type: Type of entity (e.g., "camera", "sensor", "image")
        entity_name: The entity name from the config entry
        entry_id: The config entry ID

    Returns:
        str: Unique ID for the entity
    """
    name_sanitized = entity_name.lower().replace(" ", "_").replace("-", "_")
    unique_suffix = entry_id.split("-")[0]
    return f"{entity_type}_tibber_graph_{name_sanitized}_{unique_suffix}"


async def get_config_entry_for_device_entity(
    hass: HomeAssistant, entity_id: str, domain: str
) -> ConfigEntry | None:
    """Get the config entry for any entity (camera, image, or sensor) belonging to the same device.

    This allows services to accept any entity from the Tibber Graph device, not just the camera.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID (can be camera, image, or sensor)
        domain: The integration domain (e.g., "tibber_graph")

    Returns:
        ConfigEntry if found, None otherwise
    """
    entity_registry = er.async_get(hass)
    entity_entry = entity_registry.async_get(entity_id)

    if not entity_entry:
        return None

    # Check if the entity belongs to this integration
    if entity_entry.platform != domain:
        return None

    # Get the config entry
    config_entry = hass.config_entries.async_get_entry(entity_entry.config_entry_id)
    return config_entry


def validate_sensor_entity(hass: HomeAssistant, entity_id: str | None) -> tuple[bool, str | None]:
    """Validate that an entity ID is a sensor and exists.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to validate (can be None)

    Returns:
        tuple: (is_valid, error_key) where error_key is None if valid
    """
    if not entity_id:
        return True, None

    if not isinstance(entity_id, str):
        return False, "not_sensor_entity"

    entity_id = entity_id.strip()
    if not entity_id:
        return True, None

    # Check entity registry first
    entity_registry = er.async_get(hass)
    entity_entry = entity_registry.async_get(entity_id)

    if entity_entry:
        if entity_entry.domain != "sensor":
            return False, "not_sensor_entity"
        return True, None

    # Fallback to state check
    state = hass.states.get(entity_id)
    if not state:
        return False, "entity_not_found"

    if not entity_id.startswith("sensor."):
        return False, "not_sensor_entity"

    return True, None
