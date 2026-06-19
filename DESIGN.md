# TP-Link Router Controller — Home Assistant HACS Integration

## Goal
Automatically or manually change the default gateway on a TP-Link router
based on any entity's state value (e.g. ISP Health Monitor's selected IP).

## Architecture

```
Any Source Entity                     TP-Link Router Controller
┌──────────────────┐                  ┌─────────────────────────────┐
│ sensor/input     │──state change──▶ │ State listener              │
│ (gateway IP)     │                  │                             │
└──────────────────┘                  │ TP-Link API Client          │
                                      │ ├─ Login (RSA+AES)          │
                                      │ ├─ Read LAN gateway         │
                                      │ ├─ Set LAN gateway          │
                                      │ ├─ Read DHCP gateway        │
                                      │ └─ Set DHCP gateway (opt)   │
                                      │                             │
                                      │ Entities:                   │
                                      │ ├─ sensor.gateway_status    │
                                      │ ├─ sensor.last_applied_gw   │
                                      │ ├─ sensor.current_lan_gw    │
                                      │ ├─ sensor.current_dhcp_gw   │
                                      │ ├─ button.apply_gateway     │
                                      │ └─ button.refresh_gateways  │
                                      └─────────────────────────────┘
```

## Authentication
Uses `tplinkrouterc6u` library which handles TP-Link's encrypted API:
1. Fetch RSA public key from router
2. RSA-encrypt admin password
3. Send login request → get `stok` token + `sysauth` cookie
4. Use token for subsequent API calls with AES-encrypted payloads

## API Endpoints
- LAN config: `admin/network?form=lan_ipv4` (read/write)
- DHCP config: `admin/dhcps?form=setting` (read/write)

## Queue/Debounce Logic
- `asyncio.Lock` prevents concurrent router updates
- If update in progress, new gateway IP stored as pending
- After completion, checks pending — applies if different from last applied
- No-op if requested IP matches last applied gateway

## File Structure
```
custom_components/router_gateway/
├── __init__.py        # Setup, state listener, apply_gateway with queue
├── manifest.json
├── const.py
├── config_flow.py     # Router IP, password, source entity, DHCP gateway
├── tplink_client.py   # TP-Link API with status callbacks
├── sensor.py          # Status, last applied, current LAN/DHCP gateways
├── button.py          # Apply gateway, refresh gateway values
├── strings.json
└── translations/en.json
```

## Dependencies
- `tplinkrouterc6u` — handles TP-Link RSA+AES encryption and auth
