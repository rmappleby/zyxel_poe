from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo
from . import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up switch entities for Zyxel PoE ports."""
    host = entry.data["host"]
    poe_data = hass.data[DOMAIN][host]

    entities = []
    for port in poe_data.ports:
        entities.append(ZyxelPoeSwitch(poe_data, host, port))

    async_add_entities(entities, False)


class ZyxelPoeSwitch(SwitchEntity):
    """Switch entity for a Zyxel PoE port."""

    def __init__(self, poe_data, host, port):
        self._poe_data = poe_data
        self._host = host
        self._port = port
        self._attr_unique_id = f"{host}_{port}_switch"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(self._host,)},
            name=f"Zyxel {self._host}",
            manufacturer="Zyxel",
            model="PoE Switch",
        )

    @property
    def name(self):
        return f"{self._host} Port {self._port} Switch"

    @property
    def is_on(self):
        return self._poe_data.ports[self._port]["state"] == "on"

    async def async_turn_on(self):
        self._poe_data.ports[self._port]["state"] = "on"
        return await self._poe_data.change_state(self._port, 1)

    async def async_turn_off(self):
        self._poe_data.ports[self._port]["state"] = "off"
        return await self._poe_data.change_state(self._port, 0)

    async def async_update(self):
        await self._poe_data.async_update()

