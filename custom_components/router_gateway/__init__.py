import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

import ipaddress

from .const import (
    CONF_DHCP_GATEWAY,
    CONF_ROUTER_IP,
    CONF_ROUTER_PASSWORD,
    CONF_SOURCE_ENTITY,
    DOMAIN,
    STATUS_FAILED,
    STATUS_IDLE,
    STATUS_INVALID_IP,
)
from .tplink_client import TPLinkGatewayClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = TPLinkGatewayClient(
        host=f"https://{entry.data[CONF_ROUTER_IP]}",
        password=entry.data[CONF_ROUTER_PASSWORD],
    )
    connected, error_key = await hass.async_add_executor_job(client.test_connection)
    if not connected:
        _LOGGER.error("Cannot connect to router at %s: %s", entry.data[CONF_ROUTER_IP], error_key)
        return False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "entry": entry,
        "unsub_listener": None,
        "lock": asyncio.Lock(),
        "pending_gateway": None,
        "last_applied_gateway": None,
        "status": STATUS_IDLE,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _setup_state_listener(hass, entry)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def apply_gateway(hass: HomeAssistant, entry: ConfigEntry, gateway_ip: str) -> None:
    domain_data = hass.data[DOMAIN][entry.entry_id]
    lock: asyncio.Lock = domain_data["lock"]

    if lock.locked():
        domain_data["pending_gateway"] = gateway_ip
        _LOGGER.info("Update in progress, queued gateway %s", gateway_ip)
        return

    try:
        ipaddress.ip_address(gateway_ip)
    except ValueError:
        _LOGGER.error("Invalid IP received: %s", gateway_ip)
        domain_data["status"] = STATUS_INVALID_IP
        hass.bus.async_fire(f"{DOMAIN}_status_update", {"entry_id": entry.entry_id})
        domain_data["status"] = STATUS_FAILED
        hass.bus.async_fire(f"{DOMAIN}_status_update", {"entry_id": entry.entry_id})
        return

    async with lock:
        while True:
            if gateway_ip == domain_data["last_applied_gateway"]:
                _LOGGER.info("Gateway %s already applied, no-op", gateway_ip)
                return

            client: TPLinkGatewayClient = domain_data["client"]
            dhcp_gw = entry.data.get(CONF_DHCP_GATEWAY) or None

            def _status_cb(status: str) -> None:
                domain_data["status"] = status
                hass.bus.fire(f"{DOMAIN}_status_update", {"entry_id": entry.entry_id})

            success = await hass.async_add_executor_job(
                client.set_gateway, gateway_ip, dhcp_gw, _status_cb
            )

            if success:
                domain_data["last_applied_gateway"] = gateway_ip

            domain_data["status"] = STATUS_IDLE
            hass.bus.async_fire(f"{DOMAIN}_status_update", {"entry_id": entry.entry_id})

            pending = domain_data.get("pending_gateway")
            domain_data["pending_gateway"] = None
            if pending and pending != domain_data["last_applied_gateway"]:
                gateway_ip = pending
                continue
            break


def _setup_state_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    source_entity = entry.data.get(CONF_SOURCE_ENTITY)
    if not source_entity:
        return

    domain_data = hass.data[DOMAIN][entry.entry_id]

    if domain_data.get("unsub_listener"):
        domain_data["unsub_listener"]()

    @callback
    def _on_state_change(event):
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if new_state is None or new_state.state in ("unavailable", "unknown"):
            return
        if old_state and old_state.state == new_state.state:
            return
        _LOGGER.info("Source entity changed, setting gateway to %s", new_state.state)
        hass.async_create_task(apply_gateway(hass, entry, new_state.state))

    domain_data["unsub_listener"] = async_track_state_change_event(
        hass, [source_entity], _on_state_change
    )


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    domain_data = hass.data[DOMAIN].get(entry.entry_id, {})
    if domain_data.get("unsub_listener"):
        domain_data["unsub_listener"]()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
