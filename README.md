# Zyxel-PoE
This is a custom integration for Home Assistant that exposes the Power Over Ethernet capabilities of Zyxel 
GS1900 switches into Home Assistant.
The Zyxel GS1900 series switches have PoE variants supporting PoE and PoE+. Each port can be enabled/disabled 
and the power usage monitored by way of the devices web interface. Sadly Zyxel considers these to be low-end 
switches, and doesn't allow management of the PoE functionality via SNMP.
Instead we can drive the web interface programmatically to achieve a reasonable level of integration.
## Features
- Supports multiple switches
- Creates one device per physical Zyxel switch
- Discovers and creates a switch entity for each PoE port
- Discovers and creates sensor entities (one for each PoE attribute) for each PoE port
- Assigns unique IDs to all entities allowing GUI management
- Groups switch and sensor entities by device in the Home Assistant GUI
- Fully configurable by the Home Assistant GUI using the config flow — no YAML needed
- Entity names based on each switches FQDN, falls back to IPv4 address otherwise
- Supports both v1 and v2 devices
## How to install
- Copy all the files into **custom_components/zyxel_poe/**
- Restart Home Assistant
- Go to *Settings → Devices & Services → Add Integration → Zyxel PoE Switch*
- Enter the hostname (or IP address) of the switch, and a valid administration userid and password for its web interface
## Overall operation
1. User adds switch via Home Assistant Config Flow (GUI), which uses config_flow.py and manifest.json to collect the 
configuration data the integration needs
2. Home Assistant then loads __init__.py and calls its setup routine to store connection details and call switch and sensor 
platforms to set themselves up, before collecting the initial cache of state information from the switch (via Zyxel_API.py)
3. ZyxelApi authenticates with the switch and polls and/or updates port state on the switches
4. Switch entities communicate with ZyxelApi to control PoE state, and trigger an update to the cache
5. Sensor entities read metrics from the cached data
6. Home Assistant periodically schedules an update to the cache
## Major Components
1. zyxel_api.py
Encapsulates communication with the Zyxel switch via its web API/CLI.
- ZyxelApi – handles authentication and queries the switch.
- async_get_ports() – fetches details of all PoE ports (status, power draw, limits).
- async_set_poe(port, state) – enables/disables PoE on a given port.
2. __init__.py (Integration entry point)
Implements the config flow setup model.
- async_setup_entry(hass, entry) – called when a switch is added via UI.
  - Creates one HA Device per configured switch.
  - Stores a ZyxelApi instance in hass.data[DOMAIN][entry_id].
  - Forwards setup to switch and sensor platforms.
- async_unload_entry(...) – cleans up when the integration is removed.
3. switch.py (PoE control entities)
Defines entities representing each PoE port’s on/off state.
- ZyxelPoESwitch (extends SwitchEntity)
  - is_on → reflects PoE enable status.
  - async_turn_on / async_turn_off → calls ZyxelApi.async_set_poe().
  - async_update → refreshes state via ZyxelApi.async_get_ports().
- Entities are registered under the device for that host.
4. sensor.py (Port metrics entities)
Defines sensors for per-port attributes.
- ZyxelPoESensor (extends SensorEntity)
  - Exposes attributes like current power draw (W), max power (W), or port status.
  - Uses the same ZyxelApi data cache as switches.
- Entities are also registered under the switch device.
