"""
homeassistant.components.switch.template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Allows the creation of a switch that integrates other components together

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.template/
"""
import logging

from homeassistant.helpers.entity import generate_entity_id

from homeassistant.components.switch import SwitchDevice

from homeassistant.core import EVENT_STATE_CHANGED
from homeassistant.const import (
    STATE_ON,
    STATE_OFF,
    ATTR_FRIENDLY_NAME,
    CONF_VALUE_TEMPLATE)

from homeassistant.helpers.service import call_from_config

from homeassistant.util import template, slugify

from homeassistant.exceptions import TemplateError

from homeassistant.components.switch import DOMAIN

ENTITY_ID_FORMAT = DOMAIN + '.{}'

_LOGGER = logging.getLogger(__name__)

CONF_SWITCHES = 'switches'

STATE_ERROR = 'error'

ON_ACTION = 'turn_on'
OFF_ACTION = 'turn_off'

STATE_TRUE = 'True'
STATE_FALSE = 'False'

# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """ Sets up the switches. """

    switches = []
    if config.get(CONF_SWITCHES) is None:
        _LOGGER.error("Missing configuration data for switch platform")
        return False

    for device, device_config in config[CONF_SWITCHES].items():

        if device != slugify(device):
            _LOGGER.error("Found invalid key for switch.template: %s. "
                          "Use %s instead", device, slugify(device))
            continue

        if not isinstance(device_config, dict):
            _LOGGER.error("Missing configuration data for switch %s", device)
            continue

        friendly_name = device_config.get(ATTR_FRIENDLY_NAME, device)
        state_template = device_config.get(CONF_VALUE_TEMPLATE)
        on_action = device_config.get(ON_ACTION)
        off_action = device_config.get(OFF_ACTION)
        if state_template is None:
            _LOGGER.error(
                "Missing %s for switch %s", CONF_VALUE_TEMPLATE, device)
            continue

        if on_action is None or off_action is None:
            _LOGGER.error(
                "Missing action for switch %s", device)
            continue

        switches.append(
            SwitchTemplate(
                hass,
                device,
                friendly_name,
                state_template,
                on_action,
                off_action)
            )
    if not switches:
        _LOGGER.error("No switches added")
        return False
    add_devices(switches)
    return True


class SwitchTemplate(SwitchDevice):
    """ Represents a Template Switch. """

    # pylint: disable=too-many-arguments
    def __init__(self,
                 hass,
                 device_id,
                 friendly_name,
                 state_template,
                 on_action,
                 off_action):

        self.entity_id = generate_entity_id(
            ENTITY_ID_FORMAT, device_id,
            hass=hass)

        self.hass = hass
        self._name = friendly_name
        self._template = state_template
        self._on_action = on_action
        self._off_action = off_action
        self.update()

        def _update_callback(_event):
            """ Called when the target device changes state. """
            # This can be called before the entity is properly
            # initialised, so check before updating state,
            if self.entity_id:
                self.update_ha_state(True)

        self.hass.bus.listen(EVENT_STATE_CHANGED, _update_callback)


    @property
    def name(self):
        """ Returns the name of the device. """
        return self._name

    @property
    def should_poll(self):
        """ Tells Home Assistant not to poll this entity. """
        return False

    def turn_on(self, **kwargs):
        call_from_config(self.hass, self._on_action, True)

    def turn_off(self, **kwargs):
        call_from_config(self.hass, self._off_action, True)

    @property
    def is_on(self):
        """ True if device is on. """
        return self._state == STATE_TRUE or self._state == STATE_ON

    @property
    def is_off(self):
        """ True if device is on. """
        return self._state == STATE_FALSE or self._state == STATE_OFF

    @property
    def state(self):
        """ Returns the state. """
        if self.is_on:
            return STATE_ON
        if self.is_off:
            return STATE_OFF
        return self._state

    def update(self):
        try:
            self._state = template.render(self.hass, self._template)
        except TemplateError as ex:
            self._state = STATE_ERROR
            _LOGGER.error(ex)
