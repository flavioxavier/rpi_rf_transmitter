from __future__ import annotations
from typing import Any

from . import DOMAIN, CONF_REMOTES

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant # type: ignore
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType # type: ignore
from homeassistant.helpers.entity_platform import AddEntitiesCallback # type: ignore
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA # type: ignore
from homeassistant.components.button import ButtonEntity # type: ignore
from homeassistant.const import CONF_REPEAT, CONF_NAME, CONF_UNIQUE_ID, CONF_SERVICE_DATA # type: ignore
from homeassistant.helpers.restore_state import RestoreEntity # type: ignore



import homeassistant.helpers.config_validation as cv # type: ignore
import voluptuous as vol # type: ignore

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend({
        vol.Exclusive(CONF_REMOTES, CONF_REMOTES): vol.All(
            cv.ensure_list, [{
                vol.Required(CONF_NAME): cv.string,
                vol.Required(CONF_SERVICE_DATA): cv.ensure_list(int),
                vol.Required(CONF_REPEAT): cv.positive_int,
                vol.Optional(CONF_UNIQUE_ID): cv.string
            }]
        )
    })
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None) -> None:

    _LOGGER.debug(f"setup_platform: {config} rf remotes")
    hub = hass.data[DOMAIN]
    if not hub._online:
        _LOGGER.error("hub not online, bailing out")
        
    _LOGGER.debug(f"config: {config.get(DOMAIN)}")
    buttons = []
    for button in config.get(DOMAIN).get(CONF_REMOTES):
        buttons.append(
            GPIODButton(
                hub,
                button[CONF_NAME],
                button.get(CONF_SERVICE_DATA),
                button.get(CONF_REPEAT),
                button.get(CONF_UNIQUE_ID) or f"{DOMAIN}_{button[CONF_NAME].lower().replace(' ', '_')}"
            )
        )

    async_add_entities(buttons)


class GPIODButton(ButtonEntity, RestoreEntity):
    _attr_should_poll = False

    def __init__(self, hub, name, data, repeat, unique_id):
        _LOGGER.debug(f"GPIODButton init: {data} - {repeat} - {name} - {unique_id}")
        self._hub = hub
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._data = data
        self._repeat = repeat
        self._line = None
        
    async def async_added_to_hass(self) -> None:
        """Call when the button is added to hass."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        self._line = self._hub.add_button(self._data, self._repeat)

    async def async_will_remove_from_hass(self) -> None:
        await super().async_will_remove_from_hass()
        _LOGGER.debug(f"GPIODButton async_will_remove_from_hass")
        if self._line:
            self._line.release()

    async def async_press(self, **kwargs: Any) -> None:
        self._hub.press(self._line, self._data, self._repeat)
        self.async_write_ha_state()

