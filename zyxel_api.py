"""Zyxel PoE API layer for Home Assistant integration."""

import asyncio
import logging
import math
from random import random
from datetime import timedelta

import aiohttp
import async_timeout
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.exceptions import PlatformNotReady
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)


def encode(password_input: str) -> str:
    password = ""
    possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    _len = lenn = len(password_input)
    i = 1
    while i <= (321 - _len):
        if 0 == i % 5 and _len > 0:
            _len -= 1
            password += password_input[_len]
        elif i == 123:
            password += "0" if lenn < 10 else str(math.floor(lenn / 10))
        elif i == 289:
            password += str(lenn % 10)
        else:
            password += possible[math.floor(random() * len(possible))]
        i += 1
    return password


class ZyxelPoeData:
    def __init__(self, host, username, password, interval=DEFAULT_SCAN_INTERVAL, session: aiohttp.ClientSession = None):
        self.host = host
        self._username = username
        self._password = password
        self._session = session
        self.ports = {}
        self._url = f"http://{host}/cgi-bin/dispatcher.cgi"
        # Throttle removed here; will apply in platform
        self.async_update = self._async_update

    async def _login(self, is_retry=False):
        if not self._session:
            raise PlatformNotReady("HTTP session not set for ZyxelPoeData")
        if 'HTTP_XSSID' in [c.key for c in self._session.cookie_jar]:
            return
        _LOGGER.debug("Logging into Zyxel switch at %s", self._url)

        login_data = {
            "username": self._username,
            "password": encode(self._password),
            "login": "true;"
        }

        try:
            login_step1 = await self._session.post(self._url, data=login_data, timeout=10)
            text1 = await login_step1.text()
            _LOGGER.debug("Login step 1 returned status %s", login_step1.status)

            login_check_data = {"authId": text1.strip(), "login_chk": "true"}
            await asyncio.sleep(1)
            login_step2 = await self._session.post(self._url, data=login_check_data, timeout=10)
            text2 = await login_step2.text()

            if "OK" not in text2:
                if is_retry:
                    raise PlatformNotReady(f"Login failed: {text2}")
                _LOGGER.debug("Retrying login...")
                self._session.cookie_jar.clear()
                await self._login(is_retry=True)
        except (asyncio.TimeoutError, aiohttp.ClientError) as ex:
            raise PlatformNotReady(f"Connection error while logging in to {self._url}: {ex}") from ex
        _LOGGER.debug("Logged in successfully to %s", self.host)

    async def change_state(self, port: str, state: int, is_retry=False) -> bool:
        try:
            async with async_timeout.timeout(10):
                await self._login()
                ret = await self._session.get(self._url, params={"cmd": "773"})
                text = await ret.text()
                if not ret.ok:
                    raise PlatformNotReady(f"Failed to refresh switch: {text}")
                soup = BeautifulSoup(text, "html.parser")
                xssid_input = soup.find("input", {"name": "XSSID"})
                if not xssid_input:
                    raise PlatformNotReady("No XSSID found on the switch page")
                xssid_content = xssid_input.get("value")
        except (asyncio.TimeoutError, aiohttp.ClientError) as ex:
            raise PlatformNotReady(f"Connection error while connecting to {self._url}: {ex}") from ex

        command_data = {
            "XSSID": xssid_content,
            "portlist": port,
            "state": state,
            "portPriority": 2,
            "portPowerMode": 3,
            "portRangeDetection": 0,
            "portLimitMode": 0,
            "poeTimeRange": 20,
            "cmd": 775,
            "sysSubmit": "Apply"
        }

        try:
            async with async_timeout.timeout(10):
                await self._login()
                res = await self._session.post(self._url, data=command_data)
                text = await res.text()
                if "window.location.replace" not in text:
                    if is_retry:
                        _LOGGER.error("Cannot perform action: %s", text)
                        return False
                    self._session.cookie_jar.clear()
                    await self._login(is_retry=True)
                    return await self.change_state(port, state, is_retry=True)
        except (asyncio.TimeoutError, aiohttp.ClientError) as ex:
            raise PlatformNotReady(f"Connection error while sending command to {self._url}: {ex}") from ex
        return True

    async def _async_update(self):
        try:
            async with async_timeout.timeout(10):
                await self._login()
                ret = await self._session.get(self._url, params={"cmd": "773"})
                text = await ret.text()
                if not ret.ok:
                    raise PlatformNotReady(f"Failed to refresh switch: {text}")

                soup = BeautifulSoup(text, "html.parser")
                tables = soup.select("table")
                if len(tables) < 3:
                    raise PlatformNotReady("Unexpected HTML structure from Zyxel switch")
                table = tables[2]

                for row in table.find_all("tr"):
                    cols = row.find_all("td")
                    if len(cols) == 13:
                        _, _, port, state, pd_class, pd_priority, power_up, wide_range_detection, consuming_power_mw, max_power_mw, time_range_name, time_range_status, link_speed = map(lambda a: a.text.strip(), cols)
                    elif len(cols) == 12:
                        _, _, port, state, pd_class, pd_priority, power_up, consuming_power_mw, max_power_mw, time_range_name, time_range_status, link_speed = map(lambda a: a.text.strip(), cols)
                        wide_range_detection = "Unavailable"
                    else:
                        continue

                    state = STATE_ON if state.lower() == "enable" else STATE_OFF
                    try:
                        current_power = int(consuming_power_mw) / 1000.0
                    except Exception:
                        current_power = 0.0
                    try:
                        max_power = int(max_power_mw) / 1000.0
                    except Exception:
                        max_power = 0.0

                    self.ports[port] = {
                        "port": port,
                        "state": state,
                        "class": pd_class,
                        "priority": pd_priority,
                        "power_up": power_up,
                        "wide_range_detection": wide_range_detection,
                        "current_power_w": current_power,
                        "max_power_w": max_power,
                        "time_range_name": time_range_name,
                        "time_range_status": time_range_status,
                        "link_speed": link_speed
                    }

        except (asyncio.TimeoutError, aiohttp.ClientError) as ex:
            raise PlatformNotReady(f"Connection error while updating {self._url}: {ex}") from ex

