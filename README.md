# zyxel_poe
Xyxel make a variety of ethernet switches, many with with 802.3 Power over Ethernet (PoE) support. For some
of the ranges they integrate the management of the PoE into the switches SNMP implementation, which makes 
management from Home Assistant (HA) quite straightforward. However, switches from their less expensive ranges 
only allow management of the PoE support via the switches Web Interface, which is more problematic.

This custom integration for HA exposes the PoE capabilities of those less expensive switches into 
HA by programmatically driving the switches web interfaces. It has been tested with the Zyxel GS1900 v1 and v2, 
and should work with gs1200 series switches too. 
## Features
- Supports multiple switches
- Creates one device per physical Zyxel switch
- Discovers and creates a switch entity for each PoE port
- Discovers and creates sensor entities (one for each PoE attribute) for each PoE port
- Assigns unique IDs to all entities allowing management in the HA GUI
- Groups switch and sensor entities by device in the HA GUI
- Fully configurable by the Home Assistant GUI using the config flow — no YAML needed
- Entity names based on each switches FQDN, falls back to IPv4 address otherwise
- Tested on both gs1900 v1 and v2 devices
## How to install
- Copy all the files into **custom_components/zyxel_poe/**
- Restart Home Assistant
- Go to *Settings → Devices & Services → Add Integration → Zyxel PoE Switch*
- Enter the hostname (or IP address) of the switch, and a valid administration userid and password for its web interface
## Overall operation
1. User adds switch via Home Assistant Config Flow (GUI), which uses *`config_flow.py`* and *`manifest.json`* to collect the 
configuration data the integration needs
2. Home Assistant then loads *`__init__.py`* and calls its setup routine to store connection details and call switch and sensor 
platforms to set themselves up, before collecting the initial cache of state information from the switch (via *`zyxel_api.py`*)
3. *`zyxel_api.py`* authenticates with the switch and updates port states or refreshes the state cache from the switch
4. Switch entities communicate with *`zyxel_api.py`* to control PoE state, and trigger an update to the cache
5. Sensor entities read metrics from the cached data
6. Home Assistant periodically schedules an update to the cache
## Major Components
1. *`__init__.py`* (Integration entry point)
Implements the config flow setup model
- `async_setup_entry(hass, entry)` – called when a switch is added via Home Assistant GUI.
  - Creates one Home Assistant Device per configured switch
  - Stores instances of all the data related to each switch (ie `ZyxelPoeData`) in `hass.data[DOMAIN][entry_id]`
  - Forwards setup event to switch and sensor platforms
2. *`zyxel_api.py`*
Encapsulates communication with the Zyxel switch via its web interface
- `ZyxelPoeData` – class that handles state, authentication and queries to one switch
- `async_update()` – fetches details of all PoE ports (status, power draw, limits)
- `change_state(port, state)` – enables/disables PoE on a given port
3. *`switch.py`* (PoE control entities)
Defines entities representing each PoE port’s on/off state
- Switch entities are registered under the device associated with that host.
- `ZyxelPoESwitch` (extends SwitchEntity)
  - is_on reflects if PoE is enabled
  - `async_turn_on()` / `async_turn_off` call `ZyxelPoeData.change_state()`
  - `async_update()` refreshes state via `ZyxelPoeData.async_update()`
4. *`sensor.py`* (Port metrics entities)
Defines sensors for per-port attributes.
- Sensor entities are also registered under the device associated with that host.
- `ZyxelPoESensor` (extends SensorEntity)
  - Exposes attributes like current power draw (W), max power (W), or port status.
  - Uses the same `ZyxelPoeData` data cache as switches.
## Testing
Seems to work successfully on:
- Home Assistant Container, Core 2025.10.2, Frontend 20251001.2
- Zyxel GS1900-24HPv1 running the latest firmware (V2.70(AAHM.3) dated 07/26/2022)
- Zyxel GS1900-24HPv2 running the latest firmware (V2.80(ABTP.0) dated 10/16/2023)

## Acknowledgements
[Convenience script for managing PoE on Zyxel GS1900 switches](https://github.com/jonbulica99/zyxel-poe-manager)

[Home Assistant integration for Zyxel GS1900 switches](https://github.com/lukas-hetzenecker/home-assistant-zyxel-poe)

[Home Assistant integration for Zyxel GS1200-5HP switches](https://github.com/firepinn/ha-zyxel-poe)
