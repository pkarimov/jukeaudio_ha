import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTime,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .hub import JukeAudioHub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup the config entry for my device."""

    hub: JukeAudioHub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities = []

    entities.append(SignalStrength(hub, coordinator, config_entry))
    entities.append(ConnectionType(hub, coordinator, config_entry))
    entities.append(SSID(hub, coordinator, config_entry))
    entities.append(Uptime(hub, coordinator, config_entry))
    entities.append(CpuUsage(hub, coordinator, config_entry))
    entities.append(DiskUsage(hub, coordinator, config_entry))
    entities.append(RamUsage(hub, coordinator, config_entry))

    if entities:
        async_add_entities(entities)


class JukeAudioSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for our sensors"""

    _attr_has_entity_name = True

    def __init__(self, hub: JukeAudioHub, coordinator, config_entry) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
        )
        self._hub = hub
        self._config_entry = config_entry

    @property
    def device_info(self) -> DeviceInfo:
        return self._hub.juke.device_info

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()


class SignalStrength(JukeAudioSensorBase):
    """Signal Strenth sensor"""

    device_class = SensorDeviceClass.SIGNAL_STRENGTH
    state_class = SensorStateClass.MEASUREMENT
    native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    entity_category = EntityCategory.DIAGNOSTIC
    icon = "mdi:signal"

    @property
    def unique_id(self) -> str:
        return f"{self._hub.juke.uid_base}_signal_strength"

    @property
    def native_value(self):
        if self._hub.juke.connection_info is None:
            return None
        return self._hub.juke.connection_info["signal_strength"]

    @property
    def name(self) -> str:
        return "Signal Strength"


class ConnectionType(JukeAudioSensorBase):
    """Connection Type sensor"""

    device_class = SensorDeviceClass.ENUM
    entity_category = EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return f"{self._hub.juke.uid_base}_connection_type"

    @property
    def native_value(self):
        if self._hub.juke.connection_info is None:
            return None
        return self._hub.juke.connection_info["type"]

    @property
    def name(self) -> str:
        return "Connection Type"


class SSID(JukeAudioSensorBase):
    """SSID sensor"""

    device_class = SensorDeviceClass.ENUM
    entity_category = EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return f"{self._hub.juke.uid_base}_ssid"

    @property
    def native_value(self):
        if self._hub.juke.connection_info is None:
            return None
        return self._hub.juke.connection_info["ssid"]

    @property
    def name(self) -> str:
        return "SSID"


class Uptime(JukeAudioSensorBase):
    """Uptime sensor"""

    device_class = SensorDeviceClass.DURATION
    native_unit_of_measurement = UnitOfTime.SECONDS
    entity_category = EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return f"{self._hub.juke.uid_base}_uptime"

    @property
    def native_value(self):
        if self._hub.juke.connection_info is None:
            return None
        return self._hub.juke.connection_info["uptime"]

    @property
    def name(self) -> str:
        return "Uptime"


class CpuUsage(JukeAudioSensorBase):
    """CPU Usage sensor"""

    native_unit_of_measurement = PERCENTAGE
    entity_category = EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return f"{self._hub.juke.uid_base}_cpu_usage"

    @property
    def native_value(self):
        if self._hub.juke.device_metrics is None:
            return None
        return self._hub.juke.device_metrics["cpu_usage"]

    @property
    def name(self) -> str:
        return "CPU Usage"


class DiskUsage(JukeAudioSensorBase):
    """Disk Usage sensor"""

    native_unit_of_measurement = PERCENTAGE
    entity_category = EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return f"{self._hub.juke.uid_base}_disk_usage"

    @property
    def native_value(self):
        if self._hub.juke.device_metrics is None:
            return None
        return self._hub.juke.device_metrics["disk_usage"]

    @property
    def name(self) -> str:
        return "Disk Usage"


class RamUsage(JukeAudioSensorBase):
    """RAM Usage sensor"""

    native_unit_of_measurement = PERCENTAGE
    entity_category = EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return f"{self._hub.juke.uid_base}_ram_usage"

    @property
    def native_value(self):
        if self._hub.juke.device_metrics is None:
            return None
        return self._hub.juke.device_metrics["ram_usage"]

    @property
    def name(self) -> str:
        return "RAM Usage"
