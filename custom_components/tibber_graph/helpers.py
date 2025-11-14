"""Helper functions for Tibber Graph component."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


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
