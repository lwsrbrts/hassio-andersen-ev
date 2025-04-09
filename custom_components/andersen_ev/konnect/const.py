DOMAIN = "konnect"

GRAPHQL_URL = 'https://graphql.andersen-ev.com'
GRAPHQL_USER_MAP_URL = 'https://graphql.andersen-ev.com/get-pending-user'

API_DEVICES_URL = 'https://mobile.andersen-ev.com/api/getDevices'

GRAPHQL_RUN_COMMAND_QUERY = 'mutation runAEVCommand($deviceId: ID!, $functionName: String!, $params: String) {\n  runAEVCommand(deviceId: $deviceId, functionName: $functionName, params: $params) {\n    return_value\n    __typename\n  }\n}'
GRAPHQL_DEVICE_CHARGE_LOGS_QUERY = 'query getDeviceCalculatedChargeLogs($id: ID!, $limit: Int, $offset: Int, $minEnergy: Float, $dateFrom: Date) {\n  getDevice(id: $id) {\n    id\n    deviceCalculatedChargeLogs(\n      limit: $limit\n      offset: $offset\n      minEnergy: $minEnergy\n      dateFrom: $dateFrom\n    ) {\n      chargeCostTotal\n      chargeEnergyTotal\n      deviceId\n      duration\n      gridCostTotal\n      gridEnergyTotal\n      particleFwVersion\n      solarEnergyTotal\n      solarCostTotal\n      startDateTimeLocal\n      surplusUsedCostTotal\n      surplusUsedEnergyTotal\n      uuid\n      __typename\n    }\n    __typename\n  }\n}'
GRAPHQL_DEVICE_STATUS_QUERY = 'query getDeviceStatusSimple($id: ID!) {\n  getDevice(id: $id) {\n    deviceStatus {\n      id\n      online\n      evseState\n      sysChargingEnabled\n      sysUserLock\n      sysScheduleLock\n      sysProductName\n      sysProductId\n      sysHwVersion\n      evseHwVersion\n      chargeStatus {\n        start\n        chargeEnergyTotal\n        solarEnergyTotal\n        gridEnergyTotal\n        chargePower\n        chargePowerMax\n        solarPower\n        gridPower\n        duration\n      }\n    }\n  }\n}'