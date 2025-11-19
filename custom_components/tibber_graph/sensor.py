"""Sensor platform for Tibber Graph component."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_ENTITY_NAME,
    CONF_PRICE_ENTITY_ID,
    CONF_REFRESH_MODE,
    REFRESH_MODE_SYSTEM_INTERVAL,
    REFRESH_MODE_INTERVAL,
)
from .helpers import get_unique_id

if TYPE_CHECKING:
    from datetime import datetime

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tibber Graph sensor from a config entry."""
    entity_name = entry.data.get(CONF_ENTITY_NAME, entry.title or "Tibber Graph")

    # Get the camera entity's unique ID to link the sensor
    camera_unique_id = get_unique_id("camera", f"{entity_name}", entry.entry_id)

    _LOGGER.info("Setting up Tibber Graph last update sensor for %s", entity_name)
    async_add_entities([TibberGraphLastUpdateSensor(hass, entry, entity_name, camera_unique_id)])


class TibberGraphLastUpdateSensor(SensorEntity):
    """Sensor that tracks the last update timestamp for a Tibber Graph camera."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_has_entity_name = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, entity_name: str, camera_unique_id: str):
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._entity_name = entity_name
        self._camera_unique_id = camera_unique_id
        self._triggered_by = None  # Track triggered_by separately

        self._attr_name = f"Tibber Graph {entity_name} Last Update"
        self._attr_unique_id = get_unique_id("sensor", f"{entity_name}_last_update", entry.entry_id)
        self._attr_native_value = None
        self._camera_entity_id = None

        # Get price entity ID from config (None if using Tibber integration)
        self._price_entity_id = entry.data.get(CONF_PRICE_ENTITY_ID)
        self._attr_extra_state_attributes = self._build_attributes()

        # Set up device info to group camera and sensor together
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}")},
            name=f"Tibber Graph {entity_name}",
            manufacturer="stefanes",
            model="Tibber Graph",
            entry_type=None,
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # Find the camera entity ID
        entity_registry = er.async_get(self.hass)

        # Search for camera entity with matching unique_id
        for entity_entry in er.async_entries_for_config_entry(entity_registry, self._entry.entry_id):
            if entity_entry.unique_id == self._camera_unique_id:
                self._camera_entity_id = entity_entry.entity_id
                _LOGGER.debug("Found camera entity: %s for sensor %s", self._camera_entity_id, self.entity_id)
                break

        if not self._camera_entity_id:
            _LOGGER.warning("Could not find camera entity with unique_id %s for sensor %s",
                          self._camera_unique_id, self.entity_id)
            return

        # Update attributes now that we have access to hass.states
        self._attr_extra_state_attributes = self._build_attributes()

        # Get initial value
        await self._async_update_from_camera()

        # Register state change listener for updates
        self.async_on_remove(
            self.hass.bus.async_listen(
                "tibber_graph_updated",
                self._handle_camera_update,
            )
        )

    @callback
    def _handle_camera_update(self, event) -> None:
        """Handle camera update event."""
        if event.data.get("entity_id") == self._camera_entity_id:
            timestamp = event.data.get("timestamp")
            triggered_by = event.data.get("triggered_by")
            if timestamp:
                self._attr_native_value = timestamp
                # Store triggered_by
                if triggered_by:
                    self._triggered_by = triggered_by
                # Rebuild attributes to include triggered_by and updated data source info
                self._attr_extra_state_attributes = self._build_attributes()
                self.async_write_ha_state()
                _LOGGER.debug("Updated %s with timestamp: %s (triggered by: %s)",
                            self.entity_id, timestamp, triggered_by or "unknown")

    async def _async_update_from_camera(self) -> None:
        """Get the current last update timestamp from the camera entity."""
        if not self._camera_entity_id:
            return

        # Try to get the timestamp from the camera entity's component
        entity_comp = self.hass.data.get("entity_components", {}).get("camera")
        if entity_comp:
            camera_entity = entity_comp.get_entity(self._camera_entity_id)
            if camera_entity and hasattr(camera_entity, "_last_update"):
                self._attr_native_value = camera_entity._last_update
                _LOGGER.debug("Retrieved initial timestamp for %s: %s",
                            self.entity_id, self._attr_native_value)

    def _build_attributes(self) -> dict[str, str]:
        """Build extra state attributes for the sensor."""
        attributes = {}

        # Data source information
        if self._price_entity_id:
            attributes["data_source_entity_id"] = self._price_entity_id
            attributes["data_source_friendly_name"] = self._get_entity_friendly_name(self._price_entity_id)
        else:
            attributes["data_source_entity_id"] = ""
            attributes["data_source_friendly_name"] = "Tibber Integration"

        # Add triggered_by if available
        if self._triggered_by:
            attributes["triggered_by"] = self._triggered_by

        # Get camera entity once for multiple attribute lookups
        camera_entity = self._get_camera_entity()

        # Add currency information from camera entity
        if camera_entity and hasattr(camera_entity, "_get_currency_with_source"):
            currency_symbol, currency_source = camera_entity._get_currency_with_source()
            attributes["currency_symbol"] = currency_symbol
            attributes["currency_source"] = currency_source

        # Add refresh_mode from entry options
        refresh_mode = self._entry.options.get(CONF_REFRESH_MODE)
        if refresh_mode:
            attributes["refresh_mode"] = refresh_mode

            # Add refresh_interval if mode is system_interval or interval
            if refresh_mode in [REFRESH_MODE_SYSTEM_INTERVAL, REFRESH_MODE_INTERVAL]:
                if camera_entity and hasattr(camera_entity, "_refresh_interval_hourly"):
                    if camera_entity._refresh_interval_hourly is not None:
                        # Convert boolean to text representation
                        attributes["refresh_interval"] = "60 minutes" if camera_entity._refresh_interval_hourly else "15 minutes"

        return attributes

    def _get_camera_entity(self):
        """Get the camera entity object (cached lookup)."""
        if not self._camera_entity_id:
            return None
        entity_comp = self.hass.data.get("entity_components", {}).get("camera")
        return entity_comp.get_entity(self._camera_entity_id) if entity_comp else None

    def _get_entity_friendly_name(self, entity_id: str) -> str:
        """Get friendly name for an entity with fallbacks."""
        state = self.hass.states.get(entity_id)

        # First try friendly_name attribute (user-customized)
        if state and state.attributes.get("friendly_name"):
            return state.attributes.get("friendly_name")

        # Fallback to entity registry
        entity_registry = er.async_get(self.hass)
        entity_entry = entity_registry.async_get(entity_id)
        if entity_entry and entity_entry.name:
            return entity_entry.name

        # Fallback to state name
        if state and state.name:
            return state.name

        return ""
