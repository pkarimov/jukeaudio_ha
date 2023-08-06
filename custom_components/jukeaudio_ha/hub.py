"""Hub for Juke Audio"""
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from jukeaudio.jukeaudio import (
    can_connect_to_juke,
    get_devices,
    get_device_connection_info,
    get_device_attributes,
    get_device_config,
    get_device_metrics,
    get_zones,
    get_zone_config,
    set_zone_input,
    get_inputs,
    get_input_config,
    get_available_inputs,
)
from .const import DOMAIN, LOGGER


class JukeAudioHub:
    """Hub class for Juke Audio"""

    def __init__(
        self,
        hass: HomeAssistant,
        ip_address: str,
        username: str,
        password: str,
    ) -> None:
        self._hass = hass
        self._ip_address = ip_address
        self._username = username
        self._password = password
        self._devices = []
        self.juke = None
        self.device_attributes = None
        self.device_config = None
        self._zones_ids = []
        self.zones = {}
        self._input_ids = []
        self.inputs = {}

    async def verify_connection(self) -> bool:
        """Test if we can connect to the host."""
        return await can_connect_to_juke(self._ip_address)

    async def get_devices(self):
        """Test if we can authenticate to the host."""
        return await get_devices(self._ip_address, self._username, self._password)

    async def initialize(self):
        """Initialize hub"""
        self._devices = await get_devices(
            self._ip_address, self._username, self._password
        )

    async def get_connection_info(self):
        """Get connection info"""
        return await get_device_connection_info(
            self._ip_address, self._username, self._password, self._devices[0]
        )

    async def _get_device_attributes(self):
        """Get device attributes"""
        return await get_device_attributes(
            self._ip_address, self._username, self._password, self._devices[0]
        )

    async def _get_device_config(self):
        """Get device config"""
        return await get_device_config(
            self._ip_address, self._username, self._password, self._devices[0]
        )

    async def get_device_metrics(self):
        """Get device metrics"""
        return await get_device_metrics(
            self._ip_address, self._username, self._password, self._devices[0]
        )

    async def _get_zones_ids(self):
        """Get zones"""
        zones = await get_zones(self._ip_address, self._username, self._password)
        return zones["zone_ids"]

    async def _get_zone_config(self, zone_id: str):
        """Get zone config"""
        return await get_zone_config(
            self._ip_address, self._username, self._password, zone_id
        )

    async def set_zone_input(self, zone_id: str, input):
        """Set zone inputs"""
        return await set_zone_input(
            self._ip_address, self._username, self._password, zone_id, input
        )

    async def _get_input_ids(self):
        """Get inputs"""
        inputs = await get_inputs(self._ip_address, self._username, self._password)
        return inputs["input_ids"]

    async def _get_input_config(self, input_id: str):
        """Get input config"""
        return await get_input_config(
            self._ip_address, self._username, self._password, input_id
        )

    async def _get_available_inputs(self, input_id: str):
        """Get available inputs"""
        return await get_available_inputs(
            self._ip_address, self._username, self._password, input_id
        )

    def _init_juke(self):
        """Init Juke device"""
        self.juke = JukeAudioDevice(self)

    async def fetch_data(self):
        """Get the data from Juke"""
        self.device_attributes = await self._get_device_attributes()
        LOGGER.debug("Juke device attributes: %s", self.device_attributes)

        self.device_config = await self._get_device_config()
        LOGGER.debug("Juke device config: %s", self.device_config)

        if self.juke is None:
            self._init_juke()
        await self.juke.fetch_data()

        self._zones_ids = await self._get_zones_ids()
        LOGGER.debug("Juke zone ids: %s", self._zones_ids)

        for zid in self._zones_ids:
            self.zones[zid] = await self._get_zone_config(zid)
            LOGGER.debug("Juke zone config for %s: %s", zid, self.zones[zid])

        self._input_ids = await self._get_input_ids()
        LOGGER.debug("Juke input ids: %s", self._input_ids)

        for iid in self._input_ids:
            self.inputs[iid] = await self._get_input_config(iid)
            self.inputs[iid]["available_inputs"] = await self._get_available_inputs(iid)
            LOGGER.debug("Juke input config for %s: %s", iid, self.inputs[iid])


class JukeAudioDevice:
    """HA device for Juke Audio"""

    def __init__(self, hub: JukeAudioHub) -> None:
        self.hub = hub
        self.config = self.hub.device_config
        self.uid_base = self.hub.device_attributes["serial_number"]
        self.connection_info = None
        self.device_metrics = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info"""
        name = self.config["name"]
        if name is None or name == "":
            name = self.hub.device_attributes["device_id"]

        return {
            "identifiers": {(DOMAIN, f"{self.hub.device_attributes['serial_number']}")},
            "name": name,
            "manufacturer": "Juke Audio",
            "sw_version": self.hub.device_attributes["firmware_version"],
        }

    async def fetch_data(self):
        """Fetch data from the Juke"""
        self.connection_info = await self.hub.get_connection_info()
        LOGGER.debug("Juke device connection info: %s", self.connection_info)
        self.device_metrics = await self.hub.get_device_metrics()
        LOGGER.debug("Juke device metrics: %s", self.device_metrics)
