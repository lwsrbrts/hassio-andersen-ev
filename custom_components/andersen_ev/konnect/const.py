DOMAIN = "konnect"

GRAPHQL_URL = 'https://graphql.andersen-ev.com'
GRAPHQL_USER_MAP_URL = 'https://graphql.andersen-ev.com/get-pending-user'

API_DEVICES_URL = 'https://mobile.andersen-ev.com/api/getDevices'

GRAPHQL_RUN_COMMAND_QUERY = '''
mutation runAEVCommand($deviceId: ID!, $functionName: String!, $params: String) {
  runAEVCommand(deviceId: $deviceId, functionName: $functionName, params: $params) {
    return_value
    __typename
  }
}
'''

GRAPHQL_DEVICE_CHARGE_LOGS_QUERY = '''
query getDeviceCalculatedChargeLogs($id: ID!, $limit: Int, $offset: Int, $minEnergy: Float, $dateFrom: Date) {
  getDevice(id: $id) {
    id
    deviceCalculatedChargeLogs(
      limit: $limit
      offset: $offset
      minEnergy: $minEnergy
      dateFrom: $dateFrom
    ) {
      chargeCostTotal
      chargeEnergyTotal
      deviceId
      duration
      gridCostTotal
      gridEnergyTotal
      particleFwVersion
      solarEnergyTotal
      solarCostTotal
      startDateTimeLocal
      surplusUsedCostTotal
      surplusUsedEnergyTotal
      uuid
      __typename
    }
    __typename
  }
}
'''

GRAPHQL_DEVICE_STATUS_QUERY = '''
query getDeviceStatusSimple($id: ID!) {
  getDevice(id: $id) {
    deviceStatus {
      id
      online
      evseState
      sysChargingEnabled
      sysUserLock
      sysScheduleLock
      sysProductName
      sysProductId
      sysHwVersion
      evseHwVersion
      chargeStatus {
        start
        chargeEnergyTotal
        solarEnergyTotal
        gridEnergyTotal
        chargePower
        chargePowerMax
        solarPower
        gridPower
        duration
      }
    }
  }
}
'''

GRAPHQL_DEVICE_INFO_QUERY = '''
query getDevice($id: ID!) {
  getDevice(id: $id) {
    id
    name
    last_ip_address
    deviceStatus {
      id
      evseState
      sysFwVersion
      sysSchEnabled
      sysUserLock
      sysScheduleLock
      sysRssi
      sysSSID
      sysLan
      sysTemperature
      sysFreeMemory
      sysRuntime
      sysHwVersion
      evseFwVersion
      evseHwVersion
      sysPhase
      sysVoltageA
      sysVoltageB
      sysVoltageC
      sysAmpA
      sysAmpB
      sysAmpC
      sysPowerA
      sysPowerB
      sysPowerC
      sysSolarPower
      sysGridPower
      sysChargePower
      cfgChargeAmpMin
      cfgChargeAmpMax
      scheduleSlotsArray {
        startHour
        startMinute
        endHour
        endMinute
        enabled
        dayMap {
          monday
          tuesday
          wednesday
          thursday
          friday
          saturday
          sunday
        }
      }
    }
    deviceInfo {
      id
      friendlyName
      schedule0Name
      schedule1Name
      schedule2Name
      schedule3Name
      schedule4Name
      address
      addressPlace
      addressDistrict
      addressPostcode
      addressCountry
      timeZoneRegion
    }
  }
}
'''