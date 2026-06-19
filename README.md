# TP-Link Router Controller for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Home Assistant custom integration to control the default gateway on TP-Link routers via their encrypted API. Automatically or manually update LAN and DHCP gateway settings based on any entity's state.

## Features

- **Automatic gateway switching** — listens to any entity and applies its state as the router's LAN gateway
- **Manual control** — button to apply gateway on demand
- **DHCP gateway support** — optionally update the DHCP server's default gateway
- **Step-by-step status** — sensor shows real-time progress of gateway updates (logging_in → reading config → updating → success/failed)
- **Last applied tracking** — sensor shows the last gateway this integration successfully set
- **Live gateway readback** — fetch current LAN and DHCP gateway values from the router on demand
- **Queue & debounce** — concurrent updates are queued; rapid changes only apply the latest value

## Supported Routers

Routers compatible with the [`tplinkrouterc6u`](https://github.com/AlexandrEroworker/tplinkrouterc6u) library, including:

- TP-Link Archer AX73
- TP-Link Archer AX5400
- Other TP-Link routers using the encrypted web API

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/deCodeIt/tp-link-router-controller-ha` with category **Integration**
4. Search for "TP-Link Router Controller" and install
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/router_gateway` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "TP-Link Router Controller"
3. Enter:
   - **Router IP Address** — your router's IP (default: 192.168.1.1)
   - **Admin Password** — router admin password
   - **Gateway Source Entity** (optional) — any entity whose state contains a gateway IP
   - **DHCP Default Gateway** (optional) — fixed IP to set as DHCP gateway during updates

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| Gateway Update Status | Sensor | Step-by-step progress of update operations |
| Last Applied Gateway | Sensor | The gateway IP last successfully applied by this integration |
| Current LAN Gateway | Sensor | Actual LAN gateway on the router (refreshed on demand) |
| Current DHCP Gateway | Sensor | Actual DHCP gateway on the router (refreshed on demand) |
| Apply Gateway Now | Button | Read source entity and apply its value as gateway |
| Refresh Gateway Values | Button | Fetch current LAN/DHCP gateway from the router |

## Usage with ISP Health Monitor

This integration pairs well with [ISP Health Monitor](https://github.com/deCodeIt/isp-health-ha). Set the **Gateway Source Entity** to `sensor.selected_isp_ip` and the router gateway will automatically switch when your best ISP changes.

## License

MIT
