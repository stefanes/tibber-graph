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

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CAMERA]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tibber Graph from a config entry."""
    # Store config entry data in hass.data for access by platforms
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Update entry title with Tibber home name if available
    if "tibber" in hass.data:
        try:
            homes = hass.data["tibber"].get_homes(only_active=True)
            if homes:
                home = homes[0]  # Use first active home
                if not home.info:
                    await home.update_info()
                home_name = home.info['viewer']['home']['appNickname'] or home.info['viewer']['home']['address'].get('address1', '')
                if home_name and entry.title != home_name:
                    hass.config_entries.async_update_entry(entry, title=home_name)
        except Exception as err:
            _LOGGER.warning("Failed to update integration title: %s", err)

    # Forward the setup to the camera platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
