# Andersen EV Chargepoint integration for Home Assistant

## Status

### Beta 0.4.0.

## Features
* Developed on an Andersen A2 device installed in 2019.
* The primary feature of this integration is that it implements a Home Assistant lock for the Andersen A2. It also pulls some useful sensors from the API using a GraphQL query. I personally don't get good results from these sensors but then, I never have from the mobile app either. 🤷🏻
* The lock state is updated almost instantly, other sensors are refreshed on a 60 second cycle.
* Uses [@iandbird's](https://github.com/IanDBird/konnect) baseline Python module and slightly modifies it to suit some additional sensors.
* Implements automatic token refresh to maintain persistent connections to the Andersen EV API.
* Provides a service to disable all charging schedules: `andersen_ev.disable_all_schedules`

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

## Future development
Frankly depends on whether or not I sell my house (with the charger).

## Changelog

### 0.4.0
* Added a service to disable all charging schedules: `andersen_ev.disable_all_schedules`
* Removed redundant enable/disable charging services (use the lock entity instead)

### 0.3.0
* Implemented automatic token refresh to fix the "No devices found" issue after 1 hour
  * This still uses a full authentication, which isn't ideal but refresh tokens just don't work. 🤷🏻‍♂️
* Added better error handling for authentication failures
* Improved logging for better troubleshooting

### 0.2.0
* Initial release