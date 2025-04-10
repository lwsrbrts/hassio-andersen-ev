"""Constants for the Andersen EV integration."""

DOMAIN = "andersen_ev"

# Configuration
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Defaults
DEFAULT_SCAN_INTERVAL = 60  # seconds

# Services
SERVICE_ENABLE_CHARGING = "enable_charging"
SERVICE_DISABLE_CHARGING = "disable_charging"

# Storage
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.auth_tokens"

# Attributes
ATTR_DEVICE_ID = "device_id"
ATTR_DURATION = "duration"
ATTR_CHARGE_COST_TOTAL = "charge_cost_total"
ATTR_CHARGE_ENERGY_TOTAL = "charge_energy_total"
ATTR_GRID_COST_TOTAL = "grid_cost_total"
ATTR_GRID_ENERGY_TOTAL = "grid_energy_total"
ATTR_SOLAR_ENERGY_TOTAL = "solar_energy_total"
ATTR_SOLAR_COST_TOTAL = "solar_cost_total"
ATTR_SURPLUS_USED_COST_TOTAL = "surplus_used_cost_total"
ATTR_SURPLUS_USED_ENERGY_TOTAL = "surplus_used_energy_total"