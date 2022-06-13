"""Moving average sensor implementation."""
from __future__ import annotations

import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from collections import deque 

from . import (
    DOMAIN, 
    PLATFORMS
)
from homeassistant.components.sensor import (
    ATTR_STATE_CLASS as SENSOR_ATTR_STATE_CLASS,
    DEVICE_CLASSES as SENSOR_DEVICE_CLASSES,
    DOMAIN as SENSOR_DOMAIN,
    PLATFORM_SCHEMA,
    STATE_CLASSES as SENSOR_STATE_CLASSES,
    SensorEntity
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    ATTR_ICON,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_UNIQUE_ID,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN
)
from homeassistant.core import (
    HomeAssistant,
    callback
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.typing import (
    ConfigType, 
    DiscoveryInfoType
)


_LOGGER = logging.getLogger(__name__)

DEFAULT_ICON = "mdi:chart-line-variant"
DEFAULT_PRECISION = 2

CONF_FILTER_WINDOW_SIZE = "window_size"
CONF_FILTER_UPDATE_INTERVAL = "update_interval"
CONF_FILTER_PRECISION = "precision"
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_domain(SENSOR_DOMAIN),
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Required(CONF_FILTER_WINDOW_SIZE): vol.All(cv.time_period, cv.positive_timedelta),
        vol.Required(CONF_FILTER_UPDATE_INTERVAL): vol.All(cv.time_period, cv.positive_timedelta),
        vol.Optional(CONF_FILTER_PRECISION, default=DEFAULT_PRECISION): vol.Coerce(int)
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Setup the sensor."""
    await async_setup_reload_service(hass, DOMAIN, PLATFORMS)

    name = config.get(CONF_NAME)
    unique_id = config.get(CONF_UNIQUE_ID)
    entity_id = config.get(CONF_ENTITY_ID)
    avg = MovingAvg(config.get(CONF_FILTER_WINDOW_SIZE), config.get(CONF_FILTER_PRECISION))

    async_add_entities([SensorMovingAvg(name, unique_id, entity_id, avg)])


class SensorMovingAvg(SensorEntity):
    """Representation of moving average sensor."""

    def __init__(self, name, unique_id, entity_id, avg) -> None:
        """Initialize sensor."""
        self._name = name
        self._attr_unique_id = unique_id
        self._entity = entity_id
        self._avg = avg
        self._unit_of_measurement = None
        self._state = None
        self._icon = None
        self._device_class = None
        self._attr_state_class = None

    @callback
    def _update_filter_sensor_state_event(self, event):
        """Handle device state changes."""
        _LOGGER.debug("Updating %s on event: %s", self._name, event)
        self._update_filter_sensor_state(event.data.get("new_state"))

    @callback
    def _update_filter_sensor_state(self, new_state):
        """Process device state changes."""
        if new_state is None:
            _LOGGER.debug("Updating %s, new_state is None", self._name)
            self._state = None
            self.async_write_ha_state()
            return

        if new_state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            self._state = new_state.state
            self.async_write_ha_state()
            return

        val = float(new_state.state)
        self._state = self._avg.update_value(val, new_state.last_updated)

        if self._icon is None:
            self._icon = new_state.attributes.get(ATTR_ICON, DEFAULT_ICON)
        if (self._device_class is None) and (new_state.attributes.get(ATTR_DEVICE_CLASS) in SENSOR_DEVICE_CLASSES):
            self._device_class = new_state.attributes.get(ATTR_DEVICE_CLASS)
        if (self._attr_state_class is None) and (new_state.attributes.get(SENSOR_ATTR_STATE_CLASS) in SENSOR_STATE_CLASSES):
            self._attr_state_class = new_state.attributes.get(SENSOR_ATTR_STATE_CLASS)
        if self._unit_of_measurement is None:
            self._unit_of_measurement = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)

        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Register callbacks."""
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._entity], self._update_filter_sensor_state_event
            )
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._icon

    @property
    def native_unit_of_measurement(self):
        """Return the unit_of_measurement of the device."""
        return self._unit_of_measurement

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {ATTR_ENTITY_ID: self._entity}

    @property
    def device_class(self):
        """Return device class."""
        return self._device_class


class MovingAvg:
    """Moving average computation."""

    def __init__(self, window: float, precision: int) -> None:
        """Initialize moving average."""
        self._window = window
        self._precision = precision
        self._data = deque()

    def update_value(self, val: float, timestamp: float) -> float:
        """Update moving average with value and timestamp."""
        self._data.append([val, timestamp])
        return self.update(timestamp)

    def update(self, timestamp: float) -> float:
        """Update moving average for timestamp."""
        tuple = self._data.popleft()
        return round(tuple[0], self._precision)
