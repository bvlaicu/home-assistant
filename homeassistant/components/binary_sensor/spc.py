"""
Support for Vanderbilt (formerly Siemens) SPC alarm systems.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.spc/
"""
import logging

from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.core import callback
from homeassistant.components.spc import (
    ATTR_DISCOVER_DEVICES, SIGNAL_UPDATE_SENSOR)

_LOGGER = logging.getLogger(__name__)


def _get_device_class(zone_type):
    from pyspcwebgw.const import ZoneType
    return {
        ZoneType.ALARM: 'motion',
        ZoneType.ENTRY_EXIT: 'opening',
        ZoneType.FIRE: 'smoke',
    }.get(zone_type)


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the SPC binary sensor."""
    if (discovery_info is None or
            discovery_info[ATTR_DISCOVER_DEVICES] is None):
        return

    async_add_entities(SpcBinarySensor(zone)
                       for zone in discovery_info[ATTR_DISCOVER_DEVICES]
                       if _get_device_class(zone.type))


class SpcBinarySensor(BinarySensorDevice):
    """Representation of a sensor based on a SPC zone."""

    def __init__(self, zone):
        """Initialize the sensor device."""
        self._zone = zone

    async def async_added_to_hass(self):
        """Call for adding new entities."""
        async_dispatcher_connect(self.hass,
                                 SIGNAL_UPDATE_SENSOR.format(self._zone.id),
                                 self._update_callback)

    @callback
    def _update_callback(self):
        """Call update method."""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        """Return the name of the device."""
        return self._zone.name

    @property
    def is_on(self):
        """Whether the device is switched on."""
        from pyspcwebgw.const import ZoneInput
        return self._zone.input == ZoneInput.OPEN

    @property
    def hidden(self) -> bool:
        """Whether the device is hidden by default."""
        # These type of sensors are probably mainly used for automations
        return True

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def device_class(self):
        """Return the device class."""
        return _get_device_class(self._zone.type)
