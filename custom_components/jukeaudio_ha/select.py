import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

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

    entities = []

    for i in hub.inputs:
        entities.append(
            Input(hub, config_entry, hub.inputs[i]["input_id"])
        )

    if entities:
        async_add_entities(entities)

class Input(SelectEntity):
    """Input sensor"""
    icon = "mdi:audio-input-stereo-minijack"

    _attr_has_entity_name = True

    def __init__(self, hub: JukeAudioHub, config_entry, input_id) -> None:
        """Initialize the sensor."""
        super().__init__()
        self._hub = hub
        self._config_entry = config_entry
        self._input_id = input_id

    @property
    def device_info(self) -> DeviceInfo:
        return self._hub.juke.device_info

    @property
    def unique_id(self) -> str:
        return f"input_{self._input_id}"

    @property
    def current_option(self):
        return self._hub.inputs[self._input_id]["type"]

    @property
    def name(self) -> str:
        return f"{self._hub.inputs[self._input_id]['name']} Input"

    @property
    def options(self):
        return self._hub.inputs[self._input_id]["available_inputs"]

    async def async_select_option(self, option: str) -> None:
        """Set input type"""
        _LOGGER.debug("Setting input type to %s for input %s", option, self._input_id)
        await self._hub.set_input_type(self._input_id, option)