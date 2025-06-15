"""Hub for Juke Audio"""
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from jukeaudio.jukeaudio_v3 import JukeAudioClientV3

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
        self.jukes = {}
        self.client = None
        self._server_device_id = None

    async def verify_connection(self) -> bool:
        """Test if we can connect to the host."""
        client = JukeAudioClientV3()
        if await client.can_connect_to_juke(self._ip_address):
            self.client = client
            return True
        else:
            return False

    async def get_devices(self):
        """Test if we can authenticate to the host."""
        return await self.client.get_devices(self._ip_address, self._username, self._password)

    async def initialize(self):
        """Initialize hub"""
        self._server_device_id = await self.client.get_server_device_id(
            self._ip_address, self._username, self._password)

    async def get_connection_info(self):
        """Get connection info"""
        return await self.client.get_device_connection_info(
            self._ip_address, self._username, self._password, self._server_device_id
        )

    async def _get_devices_info(self):
        """Get devices info"""
        return await self.client.get_devices_info(
            self._ip_address, self._username, self._password
        )

    async def _get_zones_ids(self):
        """Get zones"""
        zones = await self.client.get_zones(self._ip_address, self._username, self._password)
        return zones["zone_ids"]
    
    async def _get_zones_info(self):
        """Get zones"""
        zones = await self.client.get_zones_info(self._ip_address, self._username, self._password)
        return zones

    async def _get_zone_config(self, zone_id: str):
        """Get zone config"""
        return await self.client.get_zone_config(
            self._ip_address, self._username, self._password, zone_id
        )

    async def set_zone_input(self, zone_id: str, input):
        """Set zone inputs"""
        return await self.client.set_zone_input(
            self._ip_address, self._username, self._password, zone_id, input
        )
    
    async def set_zone_volume(self,zone_id: str, volume: int):
        """Set zone volume"""
        return await self.client.set_zone_volume(
            self._ip_address, self._username, self._password, zone_id, volume
        )

    async def _get_input_ids(self):
        """Get inputs"""
        inputs = await self.client.get_inputs(self._ip_address, self._username, self._password)
        return inputs["input_ids"]
    
    async def _get_input_info(self):
        """Get inputs"""
        inputs = await self.client.get_inputs_info(self._ip_address, self._username, self._password)
        return inputs

    async def _get_input_config(self, input_id: str):
        """Get input config"""
        return await self.client.get_input_config(
            self._ip_address, self._username, self._password, input_id
        )

    async def _get_available_inputs(self, input_id: str):
        """Get available inputs"""
        return await self.client.get_available_inputs(
            self._ip_address, self._username, self._password, input_id
        )
    
    async def set_input_type(self, input_id: str, type: str):
        """Set input type"""
        return await self.client.set_input_type(
            self._ip_address, self._username, self._password, input_id, type
        )

    async def set_input_volume(self, input_id: str, volume: int):
        """Set the volume for a specific input (0-100)."""
        return await self.client.set_input_volume(
            self._ip_address, self._username, self._password, input_id, volume
        )

    async def set_input_enabled(self, input_id: str, enabled: bool):
        """Enable or disable a specific input."""
        return await self.client.enable_input(
            self._ip_address, self._username, self._password, input_id, enabled
        )   

    async def fetch_data(self):
        if self.client is None:
            can_connect = await self.verify_connection()
            if not can_connect:
                LOGGER.error("Could not connect to Juke Audio")
                return

        return await self._fetch_data_v3()

    async def _fetch_data_v3(self):
        """Get the data from Juke"""
        devices = await self._get_devices_info()
        LOGGER.debug("Juke devices info: %s", devices)

        for device in devices:
            if self.jukes.get(device["device_id"]) is None:
                self.jukes[device["device_id"]] = JukeAudioDevice(self)
                LOGGER.debug("Initialized JukeAudioDevice for %s", device["device_id"])
            
            self.jukes[device["device_id"]].update(device)

        zones = await self._get_zones_info()
        LOGGER.debug("Juke zone info: %s", zones)

        for z in zones:
            zone_id_parts = z["zone_id"].split("-")
            zone_device_id = zone_id_parts[0]+"-"+zone_id_parts[1]
            if self.jukes.get(zone_device_id) is not None:
                juke = self.jukes[zone_device_id]
                juke.zones[z["zone_id"]] = z

        inputs = await self._get_input_info()
        LOGGER.debug("Juke input info: %s", inputs)

        for i in inputs:
            input_id_parts = i["input_id"].split("-")
            input_device_id = input_id_parts[0]+"-"+input_id_parts[1]
            if self.jukes.get(input_device_id) is not None:
                juke = self.jukes[input_device_id]
                juke.inputs[i["input_id"]] = i

class JukeAudioDevice:
    """HA device for Juke Audio"""

    def update(self, device_info) -> None:
        """Update device information"""
        self._device_id = device_info["device_id"]
        self.config = device_info["config"]
        self.connection_info = device_info["connection"]
        self.device_metrics = device_info["metrics"]
        self.device_attributes = device_info["attributes"]
        self.uid_base = self.device_attributes["serial_number"]
        self.zones = {}
        self.inputs = {}

    def __init__(self, hub: JukeAudioHub) -> None:
        self.hub = hub

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info"""
        name = self.config["name"]
        if name is None or name == "":
            name = self.device_attributes["device_id"]

        return {
            "identifiers": {(DOMAIN, f"{self.device_attributes['serial_number']}")},
            "name": name,
            "manufacturer": "Juke Audio",
            "sw_version": self.device_attributes["firmware_version"],
        }