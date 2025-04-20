# Andersen EV Integration

This integration allows you to control and monitor your Andersen EV charger within Home Assistant.

## Features

* Control charging on/off with a lock entity
* Control individual charging schedules with switch entities
* Monitor energy consumption, costs, and charging status
* Dedicated services for advanced control and information retrieval

## Setup

After installation, add the integration through the Home Assistant UI by searching for "Andersen EV" in the integrations page.

You'll need your Andersen account email and password to complete the setup.

## Usage

Once configured, the integration will create:
* Lock entity to enable/disable charging
* Switch entities for each charging schedule
* Sensor entities for energy usage, costs, and connector status

You can use these entities in automations, dashboards, and energy monitoring tools.