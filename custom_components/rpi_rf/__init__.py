"""Support for controlling GPIO pins of a device."""

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant # type: ignore
from homeassistant.helpers.typing import ConfigType # type: ignore

from .const import DOMAIN, CONF_REMOTES, CONF_PIN
from .hub import Hub

import voluptuous as vol # type: ignore
import homeassistant.helpers.config_validation as cv # type: ignore

from homeassistant.const import CONF_PATH, CONF_NAME, CONF_SERVICE_DATA, CONF_REPEAT, CONF_UNIQUE_ID # type: ignore

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema({
            vol.Optional(CONF_PATH): vol.All(cv.string, vol.PathExists())
        })
    },
    extra=vol.ALLOW_EXTRA
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the GPIO component."""
    version = getattr(hass.data["integrations"][DOMAIN], "version", 0)
    _LOGGER.debug(f"{DOMAIN} integration starting. Version: {version}")
    path = config.get(DOMAIN, {}).get(CONF_PATH)
    hub = Hub(hass, path)
    hass.data[DOMAIN] = hub

    return True

