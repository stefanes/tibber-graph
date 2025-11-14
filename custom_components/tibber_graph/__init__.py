"""Tibber Graph component for Home Assistant.

This component provides a camera entity that generates dynamic price graphs
from Tibber electricity pricing data.
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .services import async_register_services, async_unregister_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CAMERA, Platform.IMAGE, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tibber Graph from a config entry."""
    # Store config entry data in hass.data for access by platforms
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward the setup to the camera platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await async_register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

        # Unregister services if this is the last entry
        if not hass.data[DOMAIN]:
            await async_unregister_services(hass)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of a config entry - clean up PNG file."""
    from pathlib import Path
    from .helpers import get_graph_file_path
    from .const import CONF_ENTITY_NAME

    entity_name = entry.data.get(CONF_ENTITY_NAME, entry.title or "Tibber Graph")
    file_path = get_graph_file_path(hass, entity_name)

    try:
        if Path(file_path).exists():
            await hass.async_add_executor_job(Path(file_path).unlink)
            _LOGGER.info("Deleted PNG file for %s: %s", entity_name, file_path)
    except Exception as err:
        _LOGGER.warning("Failed to delete PNG file for %s: %s", entity_name, err)
