from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from . import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensor entities for Zyxel PoE ports."""
    host = entry.data["host"]
    poe_data = hass.data[DOMAIN][host]

    entities = []
    for port, attrs in poe_data.ports.items():
        for attr_name in attrs:
            entities.append(ZyxelPoeSensor(poe_data, host, port, attr_name))

    async_add_entities(entities, False)


class ZyxelPoeSensor(SensorEntity):
    """Sensor entity for a Zyxel PoE port attribute."""

    def __init__(self, poe_data, host, port, attr_name):
        self._poe_data = poe_data
        self._host = host
        self._port = port
        self._attr_name = attr_name
        self._attr_unique_id = f"{host}_{port}_{attr_name}_sensor"

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
        return f"{self._host} Port {self._port} {self._attr_name}"

    @property
    def state(self):
        return self._poe_data.ports[self._port].get(self._attr_name)

    async def async_update(self):
        await self._poe_data.async_update()

