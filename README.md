# zyxel_web_poe

[![Open zyxel_web_poe in the Home Assistant Community Store (HACS).](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=rmappleby&repository=zyxel_web_poe&category=integration)

Xyxel make a variety of ethernet switches, many with with 802.3 Power over Ethernet (PoE) support. For some
of the ranges they integrate the management of the PoE into the switches SNMP implementation, which makes 
management from Home Assistant (HA) quite straightforward. However, switches from their less expensive ranges 
only allow management of the PoE support via the switches Web Interface, which is more problematic.

This custom integration for HA exposes the PoE capabilities of those less expensive switches into 
HA by programmatically driving the switches web interfaces. It has been tested with the Zyxel GS1900 v1 and v2, 
and should work with GS1200 series switches too. 

## Features
- Supports multiple switches
- Creates one device per physical Zyxel switch
- Discovers and creates a switch entity for each PoE port
- Discovers and creates sensor entities (one for each PoE attribute) for each PoE port
- Assigns unique IDs to all entities allowing management in the HA GUI
- Groups switch and sensor entities by device in the HA GUI
- Fully configurable by the Home Assistant GUI using the config flow — no YAML needed
- Entity names based on each switches FQDN, falls back to IPv4 address otherwise
- Tested on both GS1900 v1 and v2 devices

## Installation
### Prerequisites:
- The switches web interfaces must be resolvable from your home assistant instance
- Administrator credentials (for each switch) that the integration can use

### Install via HACS (recommended)
1. Install HACS
2. Click the blue HACS button above
3. Click Download and confirm
4. Restart HA
5. Go to *Settings → Devices & Services → Add Integration → Zyxel PoE Switch*
6. Enter the hostname (or IP address) of the switch, and a valid administration userid and password for its web interface

### Install manually
1. SSH into your HA instance
2. `git clone https://github.com/rmappleby/zyxel_web_poe`
3. Navigate to `zyxel_web_poe/custom_components`
4. Move the directory `zyxel_web_poe` to your HA instance's `custom_components` directory
5. Restart your HA instance
6. Go to *Settings → Devices & Services → Add Integration → Zyxel PoE Switch*
7. Enter the hostname (or IP address) of the switch, and a valid administration userid and password for its web interface

## Operation
### How it works
1. User adds switch(es) via Home Assistant Config Flow (GUI), which uses *`config_flow.py`* and *`manifest.json`* to collect the 
configuration data the integration needs
2. Home Assistant then loads *`__init__.py`* and calls its setup routine to store connection details and call switch and sensor 
platforms to set themselves up, before collecting the initial cache of state information from the switch(es) (via *`zyxel_api.py`*)
3. *`zyxel_api.py`* authenticates with the switch(es) and updates port states or refreshes the state cache from the switch(es)
4. Switch entities communicate with *`zyxel_api.py`* to control PoE state, and trigger an update to the cache
5. Sensor entities read metrics from the cached data
6. Home Assistant periodically schedules updates to the cache

### Major Components
1. *`__init__.py`* (Integration entry point)
Implements the config flow setup model
- `async_setup_entry(hass, entry)` – called when a switch is added via Home Assistant GUI.
  - Creates one Home Assistant Device per configured switch
  - Stores instances of all the data related to each switch (ie `ZyxelPoeData`) in `hass.data[DOMAIN][entry_id]`
  - Forwards setup event to switch and sensor platforms
2. *`zyxel_api.py`*
Encapsulates communication with a Zyxel switch via its web interface
- `ZyxelPoeData` – class that handles state, authentication and queries to one switch
- `async_update()` – fetches details of all PoE ports (status, power draw, limits)
- `change_state(port, state)` – enables/disables PoE on a given port
- handles the differences between v1 and v2 devices & PoE entities
3. *`switch.py`* (PoE control entities)
Defines entities representing each PoE port’s on/off state
- Switch entities are registered under the device associated with that host.
- `ZyxelPoESwitch` (extends SwitchEntity)
  - is_on reflects if PoE is enabled
  - `async_turn_on()` / `async_turn_off()` call `ZyxelPoeData.change_state()`
  - `async_update()` refreshes state via `ZyxelPoeData.async_update()`
4. *`sensor.py`* (Port metrics entities)
Defines sensors for all the per-port attributes.
- Sensor entities are also registered under the device associated with that host.
- `ZyxelPoESensor` (extends SensorEntity)
  - Exposes attributes like current power draw (W), max power (W), or port status.
  - Uses the same `ZyxelPoeData` data cache as switches.
## Testing
Tested successfully on a network of three GS1900-24HP switches:
- Home Assistant Container, Core 2025.10.2, Frontend 20251001.2
- Zyxel GS1900-24HPv1 running the latest firmware (V2.70(AAHM.3) dated 07/26/2022)
- Zyxel GS1900-24HPv2 running the latest firmware (V2.80(ABTP.0) dated 10/16/2023)

## Acknowledgements
[Convenience script for managing PoE on Zyxel GS1900 switches](https://github.com/jonbulica99/zyxel-poe-manager)

[Home Assistant integration for Zyxel GS1900 switches](https://github.com/lukas-hetzenecker/home-assistant-zyxel-poe)

[Home Assistant integration for Zyxel GS1200-5HP switches](https://github.com/firepinn/ha-zyxel-poe)
