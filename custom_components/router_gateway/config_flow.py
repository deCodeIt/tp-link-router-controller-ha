import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_DHCP_GATEWAY,
    CONF_ROUTER_IP,
    CONF_ROUTER_PASSWORD,
    CONF_SOURCE_ENTITY,
    DEFAULT_ROUTER_IP,
    DOMAIN,
)
from .tplink_client import TPLinkGatewayClient


class RouterGatewayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        description_placeholders = {}
        if user_input is not None:
            client = TPLinkGatewayClient(
                host=f"https://{user_input[CONF_ROUTER_IP]}",
                password=user_input[CONF_ROUTER_PASSWORD],
            )
            connected, error_msg = await self.hass.async_add_executor_job(
                client.test_connection
            )
            if not connected:
                errors["base"] = "cannot_connect"
                description_placeholders["error_detail"] = error_msg
            else:
                return self.async_create_entry(
                    title=f"Router ({user_input[CONF_ROUTER_IP]})",
                    data=user_input,
                )

        defaults = user_input or {}
        return self.async_show_form(
            step_id="user",
            description_placeholders=description_placeholders,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ROUTER_IP,
                        default=defaults.get(CONF_ROUTER_IP, DEFAULT_ROUTER_IP),
                    ): str,
                    vol.Required(
                        CONF_ROUTER_PASSWORD,
                        default=defaults.get(CONF_ROUTER_PASSWORD, ""),
                    ): str,
                    vol.Optional(
                        CONF_SOURCE_ENTITY,
                        default=defaults.get(CONF_SOURCE_ENTITY, ""),
                    ): selector.EntitySelector(),
                    vol.Optional(
                        CONF_DHCP_GATEWAY,
                        default=defaults.get(CONF_DHCP_GATEWAY, ""),
                    ): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return RouterGatewayOptionsFlow(config_entry)


class RouterGatewayOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            new_data = {**self._config_entry.data, **user_input}
            self.hass.config_entries.async_update_entry(
                self._config_entry, data=new_data
            )
            return self.async_create_entry(title="", data={})

        current = self._config_entry.data
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SOURCE_ENTITY,
                        default=current.get(CONF_SOURCE_ENTITY, ""),
                    ): selector.EntitySelector(),
                    vol.Optional(
                        CONF_DHCP_GATEWAY,
                        default=current.get(CONF_DHCP_GATEWAY, ""),
                    ): str,
                }
            ),
        )
