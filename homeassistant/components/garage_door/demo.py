"""
homeassistant.components.garage_door.demo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Demo platform that has two fake garage doors.
"""
from homeassistant.components.garage_door import GarageDoorDevice
from homeassistant.const import STATE_CLOSED, STATE_OPEN


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """ Find and return demo garage doors. """
    add_devices_callback([
        DemoGarageDoor('Left Garage Door', STATE_CLOSED),
        DemoGarageDoor('Right Garage Door', STATE_OPEN)
    ])


class DemoGarageDoor(GarageDoorDevice):
    """ Provides a demo garage door. """
    def __init__(self, name, state):
        self._name = name
        self._state = state

    @property
    def should_poll(self):
        """ No polling needed for a demo garage door. """
        return False

    @property
    def name(self):
        """ Returns the name of the device if any. """
        return self._name

    @property
    def is_closed(self):
        """ True if device is closed. """
        return self._state == STATE_CLOSED

    def close_door(self, **kwargs):
        """ Close the device. """
        self._state = STATE_CLOSED
        self.update_ha_state()

    def open_door(self, **kwargs):
        """ Open the device. """
        self._state = STATE_OPEN
        self.update_ha_state()
