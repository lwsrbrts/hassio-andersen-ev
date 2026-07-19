# Andersen EV Chargepoint integration for Home Assistant
![Andersen Logo](/images/dark_logo.png)

## Status
![CI](https://github.com/HA-AndersenEV/hassio-andersen-ev/actions/workflows/ci.yml/badge.svg?branch=main)
![HA Quality Scale: Bronze](https://img.shields.io/badge/HA_Quality_Scale-Bronze-cd7f32)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/HA-AndersenEV/hassio-andersen-ev)](https://github.com/HA-AndersenEV/hassio-andersen-ev/releases)
[![Integration Usage](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.andersen_ev.total)

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Features
* Switch entities for each charging schedule allows enabling/disabling charge schedules.
* Lock entity to enable or disable the charge point.
* Provides services to:
  * Disable all charging schedules: `andersen_ev.disable_all_schedules`
  * Get detailed device information: `andersen_ev.get_device_info` (results displayed in UI)
  * Get detailed real-time device status: `andersen_ev.get_device_status` (results displayed in UI)
  * Reset RCM: `andersen_ev.reset_rcm`
* Live grid power sensors for those without smart meters.

## Installation

### HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. Add this repository as a custom repository in HACS:
   - Navigate to HACS → Integrations → Menu (⋮) → Custom repositories
   - Add `https://github.com/HA-AndersenEV/hassio-andersen-ev` as a repository
   - Select `Integration` as the category
3. Click "Add"
4. Search for "Andersen EV" in HACS and install it
5. Restart Home Assistant
6. Add the integration via the Home Assistant UI (Settings → Devices & Services → Add Integration)
7. Search for "Andersen EV" and follow the configuration steps

### Testing beta releases

To receive beta pre-releases, open this repository in HACS and enable "Show beta versions" for it.
Beta builds are published on demand via the "Cut beta" workflow and are tagged `vX.Y.Z-beta.N`.
Stable users who leave "Show beta versions" disabled are unaffected.

### Manual Installation

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

## Removal

1. In Home Assistant, go to **Settings > Devices & Services**.
2. Click the Andersen EV integration entry, then click **Delete**.
3. Restart Home Assistant.
4. (Optional) Uninstall via HACS: navigate to HACS > Integrations, find Andersen EV, and remove it.

## Contributing
Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for the branch model, commit
conventions, and release process before opening a pull request.

## Development

### pre-commit

This repo ships a `.pre-commit-config.yaml` that runs the same ruff lint and
format checks as CI (pinned to the same ruff version), so issues are caught
locally before you push. To enable it:

```bash
pip install pre-commit   # or: pip install -r requirements-dev.txt
pre-commit install
```

The hooks then run automatically on `git commit`. To run them across the
integration source on demand:

```bash
pre-commit run --all-files
```

## Acknowledgements

 * [@iandbird](https://github.com/IanDBird/konnect) - uses the Konnect module as a baseline with my own modifications.
 * [@strobejb](https://github.com/strobejb/andersen-ev) - (indirectly) uses his GraphQL schema in development of API communication.
