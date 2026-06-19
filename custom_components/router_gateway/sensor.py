import logging

from homeassistant.components.sensor import RestoreSensor, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, STATUS_IDLE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([
        GatewayStatusSensor(hass, entry),
        LastAppliedGatewaySensor(hass, entry),
        CurrentLANGatewaySensor(hass, entry),
        CurrentDHCPGatewaySensor(hass, entry),
    ])


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Router Gateway Controller",
        manufacturer="TP-Link",
    )


class GatewayStatusSensor(SensorEntity):
    _attr_icon = "mdi:progress-wrench"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"router_gateway_{entry.entry_id}_status"
        self._attr_name = "Gateway Update Status"
        self._attr_device_info = _device_info(entry)
        self._attr_native_value = STATUS_IDLE

    async def async_added_to_hass(self) -> None:
        @callback
        def _on_status_update(event):
            if event.data.get("entry_id") == self._entry.entry_id:
                domain_data = self._hass.data[DOMAIN].get(self._entry.entry_id, {})
                self._attr_native_value = domain_data.get("status", STATUS_IDLE)
                self.async_write_ha_state()

        self.async_on_remove(
            self._hass.bus.async_listen(f"{DOMAIN}_status_update", _on_status_update)
        )


class LastAppliedGatewaySensor(RestoreSensor):
    _attr_icon = "mdi:router-wireless"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"router_gateway_{entry.entry_id}_last_applied"
        self._attr_name = "Last Applied Gateway"
        self._attr_device_info = _device_info(entry)
        self._attr_native_value = None

    async def async_added_to_hass(self) -> None:
        if (last := await self.async_get_last_sensor_data()) and last.native_value:
            self._attr_native_value = last.native_value
            domain_data = self._hass.data[DOMAIN].get(self._entry.entry_id, {})
            domain_data["last_applied_gateway"] = last.native_value
        @callback
        def _on_status_update(event):
            if event.data.get("entry_id") == self._entry.entry_id:
                domain_data = self._hass.data[DOMAIN].get(self._entry.entry_id, {})
                applied = domain_data.get("last_applied_gateway")
                if applied and applied != self._attr_native_value:
                    self._attr_native_value = applied
                    self.async_write_ha_state()

        self.async_on_remove(
            self._hass.bus.async_listen(f"{DOMAIN}_status_update", _on_status_update)
        )


class CurrentLANGatewaySensor(RestoreSensor):
    _attr_icon = "mdi:lan"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"router_gateway_{entry.entry_id}_current_lan"
        self._attr_name = "Current LAN Gateway"
        self._attr_device_info = _device_info(entry)
        self._attr_native_value = None

    async def async_added_to_hass(self) -> None:
        if (last := await self.async_get_last_sensor_data()) and last.native_value:
            self._attr_native_value = last.native_value

        @callback
        def _on_refresh(event):
            if event.data.get("entry_id") == self._entry.entry_id:
                self._hass.async_create_task(self._fetch())

        self.async_on_remove(
            self._hass.bus.async_listen(f"{DOMAIN}_refresh_gateways", _on_refresh)
        )

    async def _fetch(self) -> None:
        client = self._hass.data[DOMAIN][self._entry.entry_id]["client"]
        value = await self._hass.async_add_executor_job(client.get_lan_gateway)
        self._attr_native_value = value
        self.async_write_ha_state()


class CurrentDHCPGatewaySensor(RestoreSensor):
    _attr_icon = "mdi:ip-network"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"router_gateway_{entry.entry_id}_current_dhcp"
        self._attr_name = "Current DHCP Gateway"
        self._attr_device_info = _device_info(entry)
        self._attr_native_value = None

    async def async_added_to_hass(self) -> None:
        if (last := await self.async_get_last_sensor_data()) and last.native_value:
            self._attr_native_value = last.native_value

        @callback
        def _on_refresh(event):
            if event.data.get("entry_id") == self._entry.entry_id:
                self._hass.async_create_task(self._fetch())

        self.async_on_remove(
            self._hass.bus.async_listen(f"{DOMAIN}_refresh_gateways", _on_refresh)
        )

    async def _fetch(self) -> None:
        client = self._hass.data[DOMAIN][self._entry.entry_id]["client"]
        value = await self._hass.async_add_executor_job(client.get_dhcp_gateway)
        self._attr_native_value = value
        self.async_write_ha_state()
