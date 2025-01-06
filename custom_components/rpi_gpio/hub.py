from __future__ import annotations

from . import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, EVENT_HOMEASSISTANT_START
from homeassistant.exceptions import HomeAssistantError

import time
from typing import Dict
from datetime import timedelta
import gpiod

from gpiod.line import Direction, Value, Bias, Drive, Edge, Clock
EventType = gpiod.EdgeEvent.Type

BIAS = { 
    "UP": Bias.PULL_UP, 
    "DOWN": Bias.PULL_DOWN,
    "DISABLED": Bias.DISABLED,
    "AS_IS": Bias.AS_IS,
}
DRIVE = { 
    "OPEN_DRAIN": Drive.OPEN_DRAIN, 
    "OPEN_SOURCE": Drive.OPEN_SOURCE, 
    "PUSH_PULL": Drive.PUSH_PULL, 
} 

class Hub:

    def __init__(self, hass: HomeAssistant, path: str, gpio: int) -> None:
        """GPIOD Hub"""

        self._path = path
        self._chip :  gpiod.Chip
        self._name = path
        self._id = path
        self._hass = hass
        self._online = False
        self._port = gpio


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

        if not gpio:
            self._port = 17


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
        if not "pinctrl" in info.label:
            _LOGGER.debug(f"verify_gpiochip: {path} no pinctrl {info.label}")
            return False

        _LOGGER.debug(f"verify_gpiochip gpiodevice: {path} has pinctrl")
        return True

    @property
    def hub_id(self) -> str:
        """ID for hub"""
        return self._id

    def add_switch(self, port, active_low, bias, drive_mode, init_state) -> gpiod.LineRequest:
        _LOGGER.debug(f"add_switch - port: {port}, active_low: {active_low}, bias: {bias}, drive_mode: {drive_mode}, init_state: {init_state}")
        self.verify_online()
        self.verify_port_ready(port)

        line_request = self._chip.request_lines(
            consumer=DOMAIN,
            config={port: gpiod.LineSettings(
            direction = Direction.OUTPUT,
            bias = BIAS[bias],
            drive = DRIVE[drive_mode],
            active_low = active_low,
            output_value = Value.ACTIVE if init_state is not None and init_state else Value.INACTIVE)})
        _LOGGER.debug(f"add_switch line_request: {line_request}")
        return line_request

    def turn_on(self, line, port) -> None:
        _LOGGER.debug(f"in turn_on {port}")
        self.verify_online()
        line.set_value(port, Value.ACTIVE)

    def turn_off(self, line, port) -> None:
        _LOGGER.debug(f"in turn_off {port}")
        self.verify_online()
        line.set_value(port, Value.INACTIVE)

    def add_button(self, data, repeat) -> gpiod.LineRequest:
        _LOGGER.debug(f"add_button - code: {data}, repeat: {repeat}")
        self.verify_online()
        port = self._port

        line_request = self._chip.request_lines(
            consumer=DOMAIN,
            config={port: gpiod.LineSettings(
            direction = Direction.OUTPUT)})
        _LOGGER.debug(f"add_switch line_request: {line_request}")
        return line_request
    
    def press(self, line, data, repeat) -> None:
        port = self._port
        _LOGGER.debug(f"send value {data} to {port} {repeat} times")
        self.verify_online()
        self.transmit_raw(line, data, repeat)

    def transmit_raw(self, line, data , repeat,):
        port = self._port
        for _ in range(repeat):
            for signal in data:
                self.transmit_signal(line, signal)
            line.set_value(port, Value.INACTIVE)
            time.sleep(0.01) # change to config option


    def transmit_signal(self, line, data):
        port = self._port
        signal = int(data)
        delay = abs(signal) / 1000000.0
        value = Value.ACTIVE if signal > 0 else Value.INACTIVE

        line.set_value(port, value)
        
        time.sleep(delay)

    