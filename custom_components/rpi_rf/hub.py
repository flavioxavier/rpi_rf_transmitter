from __future__ import annotations

from . import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant # type: ignore
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, EVENT_HOMEASSISTANT_START # type: ignore
from homeassistant.exceptions import HomeAssistantError # type: ignore

from  time import sleep
import gpiod # type: ignore

from gpiod.line import Direction, Value # type: ignore
EventType = gpiod.EdgeEvent.Type


class Hub:

    def __init__(self, hass: HomeAssistant, path: str) -> None:
        """GPIOD Hub"""

        self._path = path
        self._chip : gpiod.Chip
        self._name = path
        self._id = path
        self._hass = hass
        self._online = False
        self._port = 17


        if path:
            # use config
            _LOGGER.debug(f"trying to use configured device: {path}")
            if self.verify_gpiochip(path):
                self._online = True
                self._path = path
        else:
            # discover
            _LOGGER.debug(f"auto discovering gpio device")
            for d in [0,4,1,2,3,5]:
                # rpi3,4 using 0. rpi5 using 4
                path = f"/dev/gpiochip{d}"
                if self.verify_gpiochip(path):
                    self._online = True
                    self._path = path
                    break


        self.verify_online()
        _LOGGER.debug(f"using gpio_device: {self._path}")

    def verify_online(self):
        if not self._online:
            _LOGGER.error("No gpio device detected, bailing out")
            raise HomeAssistantError("No gpio device detected")

    def verify_gpiochip(self, path):
        if not gpiod.is_gpiochip_device(path):
            _LOGGER.debug(f"verify_gpiochip: {path} not a gpiochip_device")
            return False

        _LOGGER.debug(f"verify_gpiochip: {path} is a gpiochip_device")
        self._chip = gpiod.Chip(path)
        info = self._chip.get_info()
        _LOGGER.debug(f"{info.name} [{info.label}] ({info.num_lines} lines)")
        if not "pinctrl" in info.label:
            _LOGGER.debug(f"verify_gpiochip: {path} no pinctrl {info.label}")
            return False

        _LOGGER.debug(f"verify_gpiochip gpiodevice: {path} has pinctrl")
        return True

    @property
    def hub_id(self) -> str:
        """ID for hub"""
        return self._id

    
    def press(self, data, repeat) -> None:
        self.verify_online()
        self.transmit_raw(data, repeat)

    def transmit_raw(self, data , repeat):
        port = self._port
        _LOGGER.debug(f"send value {data} to gpio{port} {repeat} times")

        line = self._chip.request_lines(
            consumer=DOMAIN,
            config={port: gpiod.LineSettings(direction = Direction.OUTPUT, output_value=Value.INACTIVE)}
        )
        _LOGGER.debug(f"line_request: {line}")

        for _ in range(repeat):
            for signal in data:
                self.transmit_signal(line, signal)
            line.set_value(port, Value.INACTIVE)
            sleep(0.01) # change to config option
        
        line.release()


    def transmit_signal(self, line, data):
        port = self._port
        signal = int(data)
        delay = abs(signal) / 1000000.0
        value = Value.ACTIVE if signal > 0 else Value.INACTIVE
        _LOGGER.debug(f"set value on  gpio{port} to {value} for {delay} seconds")
        line.set_value(port, value)
        
        sleep(delay)

    