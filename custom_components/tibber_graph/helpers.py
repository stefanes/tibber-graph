"""Helper functions for Tibber Graph component."""
from __future__ import annotations

import asyncio
import datetime
import logging
from typing import Any
from dateutil import tz
from packaging import version

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant import const as ha_const

_LOGGER = logging.getLogger(__name__)

# Reuse local timezone object
LOCAL_TZ = tz.tzlocal()


def _verify_tibber_connection_ready(tibber_connection: Any, entry_name: str, quiet: bool) -> bool:
    """Verify that Tibber connection has homes with data available.

    Args:
        tibber_connection: Tibber connection object to verify
        entry_name: Name of the Tibber Graph entry (for logging)
        quiet: If True, suppress all logging

    Returns:
        True if connection has homes with data, False otherwise
    """
    try:
        homes = tibber_connection.get_homes(only_active=True)
        if not homes:
            if not quiet:
                _LOGGER.debug(
                    "[%s] Tibber connection has no active homes",
                    entry_name,
                )
            return False

        # Check if first home has info/data
        # Note: We don't call update_info() here as it's expensive and should be done by caller
        home = homes[0]
        if not home.info:
            if not quiet:
                _LOGGER.debug(
                    "[%s] Tibber connection home has no info data yet",
                    entry_name,
                )
            return False

        return True
    except Exception as err:
        if not quiet:
            _LOGGER.debug(
                "[%s] Error verifying Tibber connection: %s",
                entry_name,
                err,
            )
        return False


def get_home_assistant_version(hass: HomeAssistant) -> version.Version:
    """Get the Home Assistant version.

    Returns:
        version.Version: Parsed Home Assistant version
    """
    return version.parse(ha_const.__version__)


async def get_tibber_connection(hass: HomeAssistant, max_retries: int = 10, entry_name: str = "", quiet: bool = False) -> Any | None:
    """Get Tibber connection from integration.

    Tries multiple methods to get the connection, adapting to different Tibber integration versions:
    1. pre-2026.1: hass.data["tibber"]
    2. 2026.1: tibber_entry.runtime_data.tibber_connection
    3. 2026.2+: tibber_entry.runtime_data.async_get_client(hass)

    Args:
        hass: Home Assistant instance
        max_retries: Maximum number of retry attempts. Use -1 for indefinite retries (default: 10)
        entry_name: Name of the Tibber Graph entry (for logging, not needed if quiet=True)
        quiet: If True, suppress all logging (default: False)

    Returns:
        Tibber connection object if found, None otherwise
    """
    attempt = 0
    wait_indefinitely = max_retries == -1

    while True:
        # Method 1: Try legacy structure (pre-2026.1) - hass.data
        if "tibber" in hass.data:
            tibber_connection = hass.data["tibber"]
            # Verify the connection has homes with data before returning
            if _verify_tibber_connection_ready(tibber_connection, entry_name, quiet):
                if not quiet:
                    _LOGGER.debug(
                        "[%s] Using Tibber integration via 'hass.data' (pre-2026.1)",
                        entry_name,
                    )
                return tibber_connection
            elif not quiet:
                _LOGGER.debug(
                    "[%s] Tibber connection found but no homes/data available yet",
                    entry_name,
                )

        # Method 2 & 3: Try runtime_data structures (2026.1+)
        tibber_entries = hass.config_entries.async_entries("tibber")
        for tibber_entry in tibber_entries:
            if not hasattr(tibber_entry, "runtime_data"):
                continue

            # Method 2: Try old OAuth structure - direct tibber_connection attribute
            if hasattr(tibber_entry.runtime_data, "tibber_connection"):
                tibber_connection = tibber_entry.runtime_data.tibber_connection
                # Verify the connection has homes with data before returning
                if _verify_tibber_connection_ready(tibber_connection, entry_name, quiet):
                    if not quiet:
                        _LOGGER.debug(
                            "[%s] Using Tibber integration via 'runtime_data.tibber_connection' (2026.1)",
                            entry_name,
                        )
                    return tibber_connection
                elif not quiet:
                    _LOGGER.debug(
                        "[%s] Tibber connection found but no homes/data available yet",
                        entry_name,
                    )

            # Method 3: Try new structure - async_get_client method
            if hasattr(tibber_entry.runtime_data, "async_get_client"):
                try:
                    tibber_connection = await tibber_entry.runtime_data.async_get_client(hass)
                    if tibber_connection:
                        # Verify the connection has homes with data before returning
                        if _verify_tibber_connection_ready(tibber_connection, entry_name, quiet):
                            if not quiet:
                                _LOGGER.debug(
                                    "[%s] Using Tibber integration via 'runtime_data.async_get_client()' (2026.2+)",
                                    entry_name,
                                )
                            return tibber_connection
                        elif not quiet:
                            _LOGGER.debug(
                                "[%s] Tibber connection found but no homes/data available yet",
                                entry_name,
                            )
                except Exception as err:
                    if not quiet:
                        _LOGGER.debug(
                            "[%s] Failed to get Tibber connection via async_get_client: %s",
                            entry_name,
                            err,
                        )

        # Check if we should continue retrying
        attempt += 1
        if not wait_indefinitely and attempt >= max_retries:
            break

        # Calculate wait time with exponential backoff (0.5s, 1s, 2s, 4s, ..., max 1800s = 30 min)
        wait_time = min(0.5 * (2 ** attempt), 1800)

        if not quiet:
            if wait_indefinitely:
                _LOGGER.debug(
                    "[%s] Tibber connection not yet available, waiting %.1fs... (attempt %d)",
                    entry_name,
                    wait_time,
                    attempt,
                )
            else:
                _LOGGER.debug(
                    "[%s] Tibber connection not yet available, waiting %.1fs... (attempt %d/%d)",
                    entry_name,
                    wait_time,
                    attempt,
                    max_retries,
                )

        await asyncio.sleep(wait_time)

    if not quiet:
        _LOGGER.warning(
            "[%s] Failed to get Tibber connection after %d attempts",
            entry_name,
            max_retries
        )

    return None


async def wait_for_tibber_integration(hass: HomeAssistant, max_retries: int = 10, entry_name: str = "", quiet: bool = False) -> bool:
    """Wait for Tibber integration to be loaded.

    During startup, integrations load in parallel and Tibber might not be loaded yet.
    This function waits and retries until the integration is available.

    Args:
        hass: Home Assistant instance
        max_retries: Maximum number of retry attempts. Use -1 for indefinite retries (default: 10)
        entry_name: Name of the Tibber Graph entry (for logging, not needed if quiet=True)
        quiet: If True, suppress all logging (default: False)

    Returns:
        True if Tibber integration is loaded, False if max retries exceeded
    """
    attempt = 0
    wait_indefinitely = max_retries == -1

    while True:
        # Check if Tibber integration is loaded
        if "tibber" in hass.config.components:
            if not quiet:
                _LOGGER.debug(
                    "[%s] Tibber integration is loaded",
                    entry_name,
                )
            return True

        # Check if we should continue retrying
        attempt += 1
        if not wait_indefinitely and attempt >= max_retries:
            if not quiet:
                _LOGGER.warning(
                    "[%s] Tibber integration not loaded after %d attempts",
                    entry_name,
                    max_retries
                )
            return False

        # Calculate wait time with exponential backoff (0.5s, 1s, 2s, 4s, ..., max 1800s = 30 min)
        wait_time = min(0.5 * (2 ** attempt), 1800)

        if not quiet:
            if wait_indefinitely:
                _LOGGER.debug(
                    "[%s] Waiting for Tibber integration to load, waiting %.1fs... (attempt %d)",
                    entry_name,
                    wait_time,
                    attempt,
                )
            else:
                _LOGGER.debug(
                    "[%s] Waiting for Tibber integration to load, waiting %.1fs... (attempt %d/%d)",
                    entry_name,
                    wait_time,
                    attempt,
                    max_retries,
                )

        await asyncio.sleep(wait_time)


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


def get_entity_friendly_name(hass: HomeAssistant, entity_id: str) -> str:
    """Get the friendly name for an entity with fallbacks.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to get friendly name for

    Returns:
        str: The friendly name, or a formatted version of the entity ID if not found
    """
    # First try getting from state attributes (includes user customizations)
    state = hass.states.get(entity_id)
    if state and state.attributes.get("friendly_name"):
        return state.attributes["friendly_name"]

    # Then try entity registry (includes original names)
    entity_registry = er.async_get(hass)
    entity_entry = entity_registry.async_get(entity_id)
    if entity_entry and entity_entry.name:
        return entity_entry.name

    # Fallback to formatted entity ID
    return entity_id.split(".")[-1].replace("_", " ").title()


async def generate_entity_name_from_tibber(hass: HomeAssistant, max_retries: int = 3, default_name: str = "Tibber Graph") -> str:
    """Generate entity name from Tibber connection.

    Attempts to get the Tibber home nickname or address from the Tibber integration.
    Falls back to the default name if Tibber connection is unavailable or fails.

    Args:
        hass: Home Assistant instance
        max_retries: Maximum number of retry attempts (default: 3)
        default_name: Default name to use if Tibber connection fails (default: "Tibber Graph")

    Returns:
        str: Generated entity name from Tibber home info or default name
    """
    try:
        # Try to get Tibber connection (limited retries)
        tibber_connection = await get_tibber_connection(hass, max_retries=max_retries, entry_name="generate_entity_name", quiet=True)
        if tibber_connection:
            homes = tibber_connection.get_homes(only_active=True)
            if homes:
                home = homes[0]
                if not home.info:
                    await home.update_info()
                # Try to get appNickname first, then address1, finally use default
                return home.info['viewer']['home']['appNickname'] or home.info['viewer']['home']['address'].get('address1', default_name)
    except Exception:
        pass

    return default_name


def validate_sensor_entity(hass: HomeAssistant, entity_id: str | None) -> tuple[bool, str | None]:
    """Validate that an entity ID is a sensor and exists.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to validate (can be None)

    Returns:
        tuple: (is_valid, error_key) where error_key is None if valid
    """
    # Handle None or empty values
    if not entity_id or (isinstance(entity_id, str) and not entity_id.strip()):
        return True, None

    if not isinstance(entity_id, str):
        return False, "not_sensor_entity"

    entity_id = entity_id.strip()

    # Check entity registry first (most reliable)
    entity_registry = er.async_get(hass)
    entity_entry = entity_registry.async_get(entity_id)

    if entity_entry:
        return (True, None) if entity_entry.domain == "sensor" else (False, "not_sensor_entity")

    # Fallback to state check if not in registry
    state = hass.states.get(entity_id)
    if not state:
        return False, "entity_not_found"

    return (True, None) if entity_id.startswith("sensor.") else (False, "not_sensor_entity")
