from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER
from .hub import JukeAudioHub

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup the config entry for my device."""

    hub: JukeAudioHub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities = []
    for zone in hub.zones:
        entities.append(
            Zone(hub, coordinator, config_entry, hub.zones[zone]["zone_id"])
        )

    if entities:
        async_add_entities(entities)


class JukeAudioMediaPlayerBase(CoordinatorEntity, MediaPlayerEntity):
    """Base class for our zone media players"""

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


class Zone(JukeAudioMediaPlayerBase):
    """Zone media player"""

    device_class = MediaPlayerDeviceClass.SPEAKER

    def __init__(self, hub: JukeAudioHub, coordinator, config_entry, zone_id) -> None:
        """Initialize the sensor."""
        super().__init__(hub, coordinator, config_entry)
        self._zone_id = zone_id

    @property
    def unique_id(self) -> str:
        return f"zone_{self._zone_id}"

    @property
    def name(self) -> str:
        return f'{self._hub.zones[self._zone_id]["name"]} Zone'

    @property
    def state(self) -> MediaPlayerState | None:
        """State of the player."""
        return MediaPlayerState.ON

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        return (
            MediaPlayerEntityFeature.SELECT_SOURCE
            | MediaPlayerEntityFeature.VOLUME_SET
        )

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        return float(self._hub.zones[self._zone_id]["volume"]) / 100.0

    @property
    def source_list(self) -> list[str]:
        """List of available input sources."""
        sources = ["None"]
        for i in self._hub.inputs:
            sources.append(self._hub.inputs[i]["name"])

        return sources

    @property
    def source(self) -> str:
        """Currently selected input source"""
        zone_inputs = self._hub.zones[self._zone_id]["input"]
        if len(zone_inputs) > 0 and zone_inputs[0] in self._hub.inputs:
            return self._hub.inputs[zone_inputs[0]]["name"]

        return "None"

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MediaType.MUSIC

    async def async_set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        LOGGER.debug("Setting volume to %s for zone %s", volume, self._zone_id)
        await self._hub.set_zone_volume(self._zone_id, int(volume*100))
        await self.async_update()

    async def async_select_source(self, source: str):
        """Select input source."""

        input_id = None
        for i in self._hub.inputs:
            if self._hub.inputs[i]["name"] == source:
                input_id = self._hub.inputs[i]["input_id"]
                break

        LOGGER.debug("Setting input to %s for zone %s", input_id, self._zone_id)
        await self._hub.set_zone_input(self._zone_id, input_id)
        await self.async_update()
