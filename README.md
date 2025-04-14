# Andersen EV Chargepoint integration for Home Assistant

![Andersen Logo](/images/dark_logo.png)

## Status

### Beta 0.5.1

## Features
* Switch entities for each charging schedule allows enabling/disabling charge schedules.
* Lock entity to enable or disable the charge point.
* Provides services to:
  * Disable all charging schedules: `andersen_ev.disable_all_schedules`
  * Get detailed device information: `andersen_ev.get_device_info` (results displayed in UI)
  * Get detailed real-time device status: `andersen_ev.get_device_status` (results displayed in UI)

## Installation
Sorry, no HACS just yet. It may come.

1. Download the repository as a zip file and extract it.
2. Copy the `andersen_ev` folder to your Home Assistant `custom_components` directory.
3. Restart Home Assistant.
4. Add the integration via the Home Assistant UI by providing your Andersen user account user name and password.

## Services
The integration provides the following services:

### disable_all_schedules
Disables all charging schedules for a specified device.

Example:
```yaml
service: andersen_ev.disable_all_schedules
data:
  device_id: "YOUR_DEVICE_ID"
```

### get_device_info
Retrieves detailed information about a device and displays the results directly in the Home Assistant UI. This service uses Home Assistant's new Action API that allows returning data to the user interface.

Example:
```yaml
service: andersen_ev.get_device_info
data:
  device_id: "YOUR_DEVICE_ID"
```

### get_device_status
Retrieves detailed real-time status of a device and displays the results directly in the Home Assistant UI. This provides more comprehensive status information than what is available through the sensors.

Example:
```yaml
service: andersen_ev.get_device_status
data:
  device_id: "YOUR_DEVICE_ID"
```

## Future development
Frankly depends on whether or not I sell my house (with the charger).

## Changelog

### 0.5.1
* Add serial number to device
* Added icons to HA brands repo (and included here).

### 0.5.0
* Added switch entities to enable/disable individual charging schedules
* Improved schedule control to sync changes between Home Assistant and the mobile app
* Fixed state synchronization when toggling switches or making changes in the mobile app
* Added better error handling for API communications

### 0.4.2
* Improved model name handling by properly retrieving it from the API response
* Fixed issue with device model display in Home Assistant

### 0.4.1
* Added custom Material Design icons for all sensors
* Added service:
  * `get_device_status` - Retrieves detailed real-time device status with results displayed in UI - enables use of response variables.

### 0.4.0
* Added services:
  * `disable_all_schedules` - Disables all charging schedules for a charge point
  * `get_device_info` - Retrieves detailed device information with results displayed in UI - enables use of response variables.
* Removed redundant enable/disable charging services (use the lock entity instead)
* Changed power sensors to display in kilowatts (kW) to match API values

### 0.3.0
* Implemented automatic token refresh to fix the "No devices found" issue after 1 hour
  * This still uses a full authentication, which isn't ideal but refresh tokens just don't work. 🤷🏻‍♂️
* Added better error handling for authentication failures
* Improved logging for better troubleshooting

### 0.2.0
* Initial release

## Acknowledgements

 * [@iandbird](https://github.com/IanDBird/konnect) - uses the Konnect module as a baseline with my own modifications.
 * [@strobejb](https://github.com/strobejb/andersen-ev) - (indirectly) uses his GraphQL schema in development of API communication.