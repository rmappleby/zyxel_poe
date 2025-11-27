import logging

from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.util import Throttle
from datetime import timedelta
from .zyxel_api import ZyxelPoeData

_LOGGER = logging.getLogger(__name__)
DEFAULT_SCAN_INTERVAL = timedelta(minutes=1)

DOMAIN = "zyxel_poe"
DATA_KEY = "zyxel_poe_devices"

async def async_setup(hass, config):
    """No YAML setup supported."""
    return True

async def async_setup_entry(hass, entry):
    """Set up Zyxel PoE device from config entry."""
    host = entry.data["host"]
    username = entry.data["username"]
    password = entry.data["password"]

    session = async_create_clientsession(hass)
    poe_data = ZyxelPoeData(host, username, password, session=session)
    poe_data.async_update = Throttle(DEFAULT_SCAN_INTERVAL)(poe_data._async_update)

    await poe_data.async_update()

    # Store the object for platform files
    hass.data.setdefault(DOMAIN, {})[host] = poe_data

    # ------------------------------------------------------------
    # FIX: await async_forward_entry_setups instead of creating tasks
    # ------------------------------------------------------------
    await hass.config_entries.async_forward_entry_setups(
        entry,
        ["switch", "sensor"],
    )

    return True
