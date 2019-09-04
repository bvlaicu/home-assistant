"""Support for Linky."""
import json
import logging
from datetime import timedelta

from pylinky.client import DAILY, MONTHLY, YEARLY, LinkyClient
from pylinky.client import PyLinkyException

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_PASSWORD,
    CONF_TIMEOUT,
    CONF_USERNAME,
    ENERGY_KILO_WATT_HOUR,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import HomeAssistantType

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=4)
ICON_ENERGY = "mdi:flash"
CONSUMPTION = "conso"
TIME = "time"
INDEX_CURRENT = -1
INDEX_LAST = -2
ATTRIBUTION = "Data provided by Enedis"

SENSORS = {
    "yesterday": ("Linky yesterday", DAILY, INDEX_LAST),
    "current_month": ("Linky current month", MONTHLY, INDEX_CURRENT),
    "last_month": ("Linky last month", MONTHLY, INDEX_LAST),
    "current_year": ("Linky current year", YEARLY, INDEX_CURRENT),
    "last_year": ("Linky last year", YEARLY, INDEX_LAST),
}
SENSORS_INDEX_LABEL = 0
SENSORS_INDEX_SCALE = 1
SENSORS_INDEX_WHEN = 2


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Old way of setting up the Linky platform."""
    pass


async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigEntry, async_add_entities
) -> None:
    """Add Linky entries."""
    account = LinkyAccount(
        entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], entry.data[CONF_TIMEOUT]
    )

    await hass.async_add_executor_job(account.update_linky_data)

    sensors = [
        LinkySensor("Linky yesterday", account, DAILY, INDEX_LAST),
        LinkySensor("Linky current month", account, MONTHLY, INDEX_CURRENT),
        LinkySensor("Linky last month", account, MONTHLY, INDEX_LAST),
        LinkySensor("Linky current year", account, YEARLY, INDEX_CURRENT),
        LinkySensor("Linky last year", account, YEARLY, INDEX_LAST),
    ]

    async_track_time_interval(hass, account.update_linky_data, SCAN_INTERVAL)

    async_add_entities(sensors, True)


class LinkyAccount:
    """Representation of a Linky account."""

    def __init__(self, username, password, timeout):
        """Initialise the Linky account."""
        self._username = username
        self._password = password
        self._timeout = timeout
        self._data = None

    def update_linky_data(self, event_time=None):
        """Fetch new state data for the sensor."""
        client = LinkyClient(self._username, self._password, None, self._timeout)
        try:
            client.login()
            client.fetch_data()
            self._data = client.get_data()
            _LOGGER.debug(json.dumps(self._data, indent=2))
        except PyLinkyException as exp:
            _LOGGER.error(exp)
        finally:
            client.close_session()

    @property
    def username(self):
        """Return the username."""
        return self._username

    @property
    def data(self):
        """Return the data."""
        return self._data


class LinkySensor(Entity):
    """Representation of a sensor entity for Linky."""

    def __init__(self, name, account: LinkyAccount, scale, when):
        """Initialize the sensor."""
        self._name = name
        self._account = account
        self._scale = scale
        self._when = when
        self._username = account.username
        self._time = None
        self._consumption = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._consumption

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ENERGY_KILO_WATT_HOUR

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_ENERGY

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "time": self._time,
            CONF_USERNAME: self._username,
        }

    async def async_update(self) -> None:
        """Retrieve the new data for the sensor."""
        data = self._account.data[self._scale][self._when]
        self._consumption = data[CONSUMPTION]
        self._time = data[TIME]

        if self._scale is not YEARLY:
            year_index = INDEX_CURRENT
            if self._time.endswith("Dec"):
                year_index = INDEX_LAST
            self._time += " " + self._account.data[YEARLY][year_index][TIME]
