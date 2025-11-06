"""Sensor platform for Tibber Graph component."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_ENTITY_NAME, CONF_PRICE_ENTITY_ID

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
    # The camera uses format: camera_tibber_graph_{name_sanitized}_{unique_suffix}
    name_sanitized = entity_name.lower().replace(" ", "_").replace("-", "_")
    unique_suffix = entry.entry_id.split("-")[0]
    camera_unique_id = f"camera_tibber_graph_{name_sanitized}_{unique_suffix}"

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

        # Create a sanitized version for unique IDs
        name_sanitized = entity_name.lower().replace(" ", "_").replace("-", "_")
        unique_suffix = entry.entry_id.split("-")[0]

        self._attr_name = f"Tibber Graph {entity_name} Last Update"
        self._attr_unique_id = f"sensor_tibber_graph_{name_sanitized}_last_update_{unique_suffix}"
        self._attr_native_value = None
        self._camera_entity_id = None

        # Get price entity ID from config (None if using Tibber integration)
        self._price_entity_id = entry.data.get(CONF_PRICE_ENTITY_ID)
        self._attr_extra_state_attributes = self._build_attributes()

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
                # Update triggered_by attribute
                if triggered_by:
                    self._attr_extra_state_attributes = {
                        **self._attr_extra_state_attributes,
                        "triggered_by": triggered_by,
                    }
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

        if self._price_entity_id:
            # Using custom entity as data source
            attributes["data_source_entity_id"] = self._price_entity_id

            # Get friendly name from entity registry first, then state, then fallback to entity_id
            entity_registry = er.async_get(self.hass)
            entity_entry = entity_registry.async_get(self._price_entity_id)

            if entity_entry and entity_entry.name:
                # Use the name from entity registry (user-customized name)
                attributes["data_source_friendly_name"] = entity_entry.name
            else:
                # Fallback to state's name or entity_id
                state = self.hass.states.get(self._price_entity_id)
                if state and state.name:
                    attributes["data_source_friendly_name"] = state.name
                else:
                    attributes["data_source_friendly_name"] = self._price_entity_id
        else:
            # Using Tibber integration as data source
            attributes["data_source_entity_id"] = ""
            attributes["data_source_friendly_name"] = "Tibber Integration"

        return attributes
