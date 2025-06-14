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
    # Add zone entities
    for zone in hub.zones:
        entities.append(
            Zone(hub, coordinator, config_entry, hub.zones[zone]["zone_id"])
        )
    
    # Add input entities
    if hub.useV3:
        for i in hub.inputs:
            if hub.inputs[i]["input_class"] == 0:
                entities.append(
                    InputMediaPlayer(hub, coordinator, config_entry, hub.inputs[i]["input_id"])
                )
    else:
        for i in hub.inputs:
            entities.append(
                InputMediaPlayer(hub, coordinator, config_entry, hub.inputs[i]["input_id"])
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

        if self._hub.useV3:
            for i in self._hub.inputs:
                if self._hub.inputs[i]["input_class"] == 0:
                    sources.append(self._hub.inputs[i]["name"])
        else:
            for i in self._hub.inputs:
                sources.append(self._hub.inputs[i]["name"])

        return sources

    @property
    def source(self) -> str:
        """Currently selected input source"""
        zone_inputs = self._hub.zones[self._zone_id]["input"]

        if self._hub.useV3:
            for input_id in zone_inputs:
                if input_id in self._hub.inputs and self._hub.inputs[input_id]["input_class"] == 0:
                    return self._hub.inputs[input_id]["name"]
        else:
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


class InputMediaPlayer(JukeAudioMediaPlayerBase):
    """Input media player"""
    
    device_class = MediaPlayerDeviceClass.RECEIVER
    
    def __init__(self, hub: JukeAudioHub, coordinator, config_entry, input_id) -> None:
        """Initialize the input media player."""
        super().__init__(hub, coordinator, config_entry)
        self._input_id = input_id
    
    @property
    def unique_id(self) -> str:
        return f"input_{self._input_id}"
    
    @property
    def name(self) -> str:
        return f"{self._hub.inputs[self._input_id]['name']} Input"
    
    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        features = MediaPlayerEntityFeature.SELECT_SOURCE | MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
        
        # Only add volume control if volume exists for this input
        input_data = self._hub.inputs[self._input_id]
        if "volume" in input_data and input_data["volume"] is not None:
            features |= MediaPlayerEntityFeature.VOLUME_SET
            
        return features
    
    @property
    def state(self) -> MediaPlayerState | None:
        """State of the player."""
        input_data = self._hub.inputs[self._input_id]
        # Check if input is enabled, defaulting to True if not present
        if input_data.get("enabled", True):
            return MediaPlayerState.ON
        else:
            return MediaPlayerState.OFF
    
    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        input_data = self._hub.inputs[self._input_id]
        if "volume" in input_data and input_data["volume"] is not None:
            return float(input_data["volume"]) / 100.0
        return None
    
    @property
    def source(self) -> str:
        """Currently selected input type."""
        if self._hub.useV3:
            return self._hub.inputs[self._input_id]["input_type"]
        else:
            return self._hub.inputs[self._input_id]["type"]
    
    @property
    def source_list(self) -> list[str]:
        """List of available input types."""
        available_types = self._hub.inputs[self._input_id]["available_types"]
        
        # Get current source by using the source property
        current_source = self.source
        
        # Add current source if not already in the list
        if current_source and current_source not in available_types:
            return available_types + [current_source]
        
        return available_types
    
    @property
    def icon(self):
        """Return dynamic icon based on input type."""
        input_type = self.source
        
        # Map input types to appropriate icons
        icon_map = {
            "Airplay2": "mdi:cast-audio-variant",
            "DLNA": "mdi:cast-audio",
            "Spotify": "mdi:spotify",
            "USB-1": "mdi:usb",
            "USB-2": "mdi:usb",
            "Bluetooth": "mdi:bluetooth-audio",
            "RCA": "mdi:audio-input-rca",
            "Optical": "mdi:laser-pointer"
        }
        
        # Return the mapped icon or a default
        return icon_map.get(input_type, "mdi:music-box")
    
    async def async_set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        LOGGER.debug("Setting volume to %s for input %s", volume, self._input_id)
        await self._hub.set_input_volume(self._input_id, int(volume*100))
        await self.async_update()
    
    async def async_select_source(self, source: str):
        """Select input type."""
        LOGGER.debug("Setting input type to %s for input %s", source, self._input_id)
        await self._hub.set_input_type(self._input_id, source)
        await self.async_update()
    
    async def async_turn_on(self) -> None:
        """Turn the input on (enable it)."""
        LOGGER.debug("Enabling input %s", self._input_id)
        await self._hub.set_input_enabled(self._input_id, True)
        await self.async_update()
    
    async def async_turn_off(self) -> None:
        """Turn the input off (disable it)."""
        LOGGER.debug("Disabling input %s", self._input_id)
        await self._hub.set_input_enabled(self._input_id, False)
        await self.async_update()
