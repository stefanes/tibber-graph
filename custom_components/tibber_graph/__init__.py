"""Tibber Graph component for Home Assistant.

This component provides a camera entity that generates dynamic price graphs
from Tibber electricity pricing data.
"""
import logging

from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.helpers import discovery

DOMAIN = "tibber_graph"
DEPENDENCIES = ["tibber"]

_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    """Set up the Tibber Graph component."""

    def ha_started(_event):
        """Load the camera platform when Home Assistant has started."""
        discovery.load_platform(hass, "camera", DOMAIN, {}, config)

    hass.bus.listen_once(EVENT_HOMEASSISTANT_START, ha_started)

    return True
