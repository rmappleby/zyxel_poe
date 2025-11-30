import voluptuous as vol
import logging

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .zyxel_api import ZyxelPoeData

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
})

class ZyxelPoeConfigFlow(config_entries.ConfigFlow, domain="zyxel_web_poe"):
    """Handle a config flow for Zyxel PoE Switch."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            session = async_create_clientsession(self.hass)
            poe_data = ZyxelPoeData(host, username, password, session=session)

            try:
                await poe_data._async_update()
            except Exception as ex:
                _LOGGER.error("Cannot connect to Zyxel PoE switch %s: %s", host, ex)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=host, data=user_input)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)

