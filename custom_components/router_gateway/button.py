import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_SOURCE_ENTITY, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([
        SetGatewayButton(hass, entry),
        RefreshGatewaysButton(hass, entry),
    ])


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Router Gateway Controller",
        manufacturer="TP-Link",
    )


class SetGatewayButton(ButtonEntity):
    _attr_icon = "mdi:swap-horizontal"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"router_gateway_{entry.entry_id}_set"
        self._attr_name = "Apply Gateway Now"
        self._attr_device_info = _device_info(entry)

    async def async_press(self) -> None:
        source_entity = self._entry.data.get(CONF_SOURCE_ENTITY)
        if not source_entity:
            _LOGGER.error("No source entity configured")
            return

        state = self._hass.states.get(source_entity)
        if state is None or state.state in ("unavailable", "unknown", "N/A"):
            _LOGGER.error("Source entity %s has no valid state", source_entity)
            return

        from . import apply_gateway
        await apply_gateway(self._hass, self._entry, state.state)


class RefreshGatewaysButton(ButtonEntity):
    _attr_icon = "mdi:refresh"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"router_gateway_{entry.entry_id}_refresh"
        self._attr_name = "Refresh Gateway Values"
        self._attr_device_info = _device_info(entry)

    async def async_press(self) -> None:
        self._hass.bus.async_fire(
            f"{DOMAIN}_refresh_gateways",
            {"entry_id": self._entry.entry_id},
        )
