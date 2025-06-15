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
from .hub import JukeAudioHub, JukeAudioDevice

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup the config entry for my device."""

    hub: JukeAudioHub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities = []    
    for juke_id in hub.jukes:
        juke = hub.jukes[juke_id]

        # Add zone entities
        for zone_id in juke.zones:
            entities.append(
                Zone(juke, coordinator, config_entry, zone_id)
            )

        # Add input entities    
        for input_id in juke.inputs:
            input = juke.inputs[input_id]
            if input["input_class"] == 0:
                entities.append(
                    InputMediaPlayer(juke, coordinator, config_entry, input_id)
                )
    if entities:
        async_add_entities(entities)


class JukeAudioMediaPlayerBase(CoordinatorEntity, MediaPlayerEntity):
    """Base class for our zone media players"""

    _attr_has_entity_name = True

    def __init__(self, juke: JukeAudioDevice, coordinator, config_entry) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
        )
        self._juke = juke
        self._config_entry = config_entry

    @property
    def device_info(self) -> DeviceInfo:
        return self._juke.device_info

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()


class Zone(JukeAudioMediaPlayerBase):
    """Zone media player"""

    device_class = MediaPlayerDeviceClass.SPEAKER

    def __init__(self, juke: JukeAudioDevice, coordinator, config_entry, zone_id) -> None:
        """Initialize the sensor."""
        super().__init__(juke, coordinator, config_entry)
        self._zone_id = zone_id

    @property
    def unique_id(self) -> str:
        return f"zone_{self._zone_id}"

    @property
    def name(self) -> str:
        return f'{self._juke.zones[self._zone_id]["name"]} Zone'

    @property
    def extra_state_attributes(self):
        """Return additional attributes for the zone."""
        attributes = {}
        
        zone_data = self._juke.zones[self._zone_id]
        
        # Add warning messages as attributes if present
        if "warnings" in zone_data and zone_data["warnings"]:
            attributes["warnings"] = zone_data["warnings"]
            attributes["warning_count"] = len(zone_data["warnings"])
            
        return attributes
    
    @property
    def state(self) -> MediaPlayerState | None:
        """State of the player."""
        # Check if there's an active input for this zone
        zone_data = self._juke.zones[self._zone_id]
        
        # If zone has an active_input that's not None, it's playing
        if "active_input" in zone_data and zone_data["active_input"] is not None:
            return MediaPlayerState.PLAYING
        
        # No active input but zone is on
        if zone_data.get("enabled", True):
            return MediaPlayerState.ON
            
        # Zone is disabled
        return MediaPlayerState.OFF
        
    @property
    def media_title(self) -> str | None:
        """Title of current playing media."""
        zone_data = self._juke.zones[self._zone_id]
        
        # Only provide title if we're playing
        if "active_input" in zone_data and zone_data["active_input"] is not None:
            active_input_id = zone_data["active_input"]
            
            # Get the name of the active input
            if active_input_id in self._juke.inputs:
                input_data = self._juke.inputs[active_input_id]
                
                # Only use input name if input class is 0
                if input_data.get("input_class") == 0:
                    input_name = input_data.get("name")
                    if input_name:
                        return f"Playing from {input_name}"
                
                # If we can't use the name, fall back to type
                input_type = input_data.get("input_type", "Unknown")
                return f"Playing from {input_type}"
                
        return None
    
    @property
    def media_artist(self) -> str | None:
        """Artist of current playing media."""
        # If there's additional metadata available from the active input
        # you could return it here
        return None
    
    @property 
    def icon(self) -> str | None:
        zone_data = self._juke.zones[self._zone_id]
        
        # Show warning icon if there are warnings
        if "warnings" in zone_data and zone_data["warnings"]:
            return "mdi:speaker-message"
        
        """Return dynamic icon based on playing state."""
        if self.state == MediaPlayerState.PLAYING:
            return "mdi:speaker-play"
        elif self.state == MediaPlayerState.ON:
            return "mdi:speaker"
        else:
            return "mdi:speaker-off"

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
        return float(self._juke.zones[self._zone_id]["volume"]) / 100.0

    @property
    def source_list(self) -> list[str]:
        """List of available input sources."""
        sources = ["None"]

        for i in self._juke.inputs:
            # Only show enabled inputs
            if (self._juke.inputs[i]["input_class"] == 0 and 
                self._juke.inputs[i].get("enabled", True)):
                sources.append(self._juke.inputs[i]["name"])

        return sources

    @property
    def source(self) -> str:
        """Currently selected input source"""
        zone_inputs = self._juke.zones[self._zone_id]["input"]

        for input_id in zone_inputs:
            if input_id in self._juke.inputs and self._juke.inputs[input_id]["input_class"] == 0:
                return self._juke.inputs[input_id]["name"]

        return "None"

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MediaType.MUSIC

    async def async_set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        LOGGER.debug("Setting volume to %s for zone %s", volume, self._zone_id)
        await self._juke.hub.set_zone_volume(self._zone_id, int(volume*100))
        await self.async_update()

    async def async_select_source(self, source: str):
        """Select input source."""

        input_id = None
        for i in self._juke.inputs:
            if self._juke.inputs[i]["name"] == source:
                input_id = self._juke.inputs[i]["input_id"]
                break

        LOGGER.debug("Setting input to %s for zone %s", input_id, self._zone_id)
        await self._juke.hub.set_zone_input(self._zone_id, input_id)
        await self.async_update()


class InputMediaPlayer(JukeAudioMediaPlayerBase):
    """Input media player"""
    
    device_class = MediaPlayerDeviceClass.RECEIVER
    
    def __init__(self, juke: JukeAudioDevice, coordinator, config_entry, input_id) -> None:
        """Initialize the input media player."""
        super().__init__(juke, coordinator, config_entry)
        self._input_id = input_id
    
    @property
    def unique_id(self) -> str:
        return f"input_{self._input_id}"
    
    @property
    def name(self) -> str:
        return f"{self._juke.inputs[self._input_id]['name']} Input"
    
    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        features = MediaPlayerEntityFeature.SELECT_SOURCE | MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
        
        # Only add volume control if volume exists for this input
        input_data = self._juke.inputs[self._input_id]
        if "volume" in input_data and input_data["volume"] is not None:
            features |= MediaPlayerEntityFeature.VOLUME_SET
            
        return features
    
    @property
    def state(self) -> MediaPlayerState | None:
        """State of the player."""
        input_data = self._juke.inputs[self._input_id]
        # Check if input is enabled, defaulting to True if not present
        if input_data.get("enabled", True):
            return MediaPlayerState.ON
        else:
            return MediaPlayerState.OFF
    
    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        input_data = self._juke.inputs[self._input_id]
        if "volume" in input_data and input_data["volume"] is not None:
            return float(input_data["volume"]) / 100.0
        return None
    
    @property
    def source(self) -> str:
        """Currently selected input type."""
        return self._juke.inputs[self._input_id]["input_type"]
    
    @property
    def source_list(self) -> list[str]:
        """List of available input types."""
        available_types = self._juke.inputs[self._input_id]["available_types"]
        
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
        await self._juke.hub.set_input_volume(self._input_id, int(volume*100))
        await self.async_update()
    
    async def async_select_source(self, source: str):
        """Select input type."""
        LOGGER.debug("Setting input type to %s for input %s", source, self._input_id)
        await self._juke.hub.set_input_type(self._input_id, source)
        await self.async_update()
    
    async def async_turn_on(self) -> None:
        """Turn the input on (enable it)."""
        LOGGER.debug("Enabling input %s", self._input_id)
        await self._juke.hub.set_input_enabled(self._input_id, True)
        await self.async_update()
    
    async def async_turn_off(self) -> None:
        """Turn the input off (disable it)."""
        LOGGER.debug("Disabling input %s", self._input_id)
        await self._juke.hub.set_input_enabled(self._input_id, False)
        await self.async_update()
