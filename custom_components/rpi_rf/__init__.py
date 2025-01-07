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
            vol.Optional(CONF_PATH): vol.All(cv.string, vol.PathExists()),
            vol.Required(CONF_PIN): cv.positive_int,
            vol.Exclusive(CONF_REMOTES, CONF_REMOTES): vol.All(
                cv.ensure_list, [{
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required(CONF_SERVICE_DATA): cv.ensure_list(int),
                    vol.Required(CONF_REPEAT): cv.positive_int,
                    vol.Optional(CONF_UNIQUE_ID): cv.string
                }]
        )
        })
    },
    extra=vol.ALLOW_EXTRA
    #vol.Optional(CONF_LIST, default=DEFAULT_LIST): vol.All(cv.ensure_list, [cv.positive_int]),
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the GPIO component."""
    version = getattr(hass.data["integrations"][DOMAIN], "version", 0)
    _LOGGER.debug(f"{DOMAIN} integration starting. Version: {version}")
    path = config.get(DOMAIN, {}).get(CONF_PATH) 
    pin = config.get(DOMAIN, {}).get(CONF_PIN) 
    hub = Hub(hass, path, pin)
    hass.data[DOMAIN] = hub

    return True

