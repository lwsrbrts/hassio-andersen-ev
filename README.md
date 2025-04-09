# hassio-andersen-ev
An attempt at a Home Assistant integration for Andersen home chargers.

This implements a simple lock for the Andersen A2 and also pulls some useful sensors from the API.

The lock state is updated almost instantly, other sensors are refreshed on a 60 second cycle.

Uses @iandbird's baseline Python module and slightly modifies it to suit some additional requirements.

