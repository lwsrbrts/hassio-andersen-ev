import asyncio
import requests
import logging
from . import const
from .bearerauth import BearerAuth

_LOGGER = logging.getLogger(__name__)

class KonnectDevice:
    api = None
    device_id = None
    friendly_name = None
    user_lock = False
    _last_status = None

    def __init__(self, api, device_id, friendly_name, user_lock):
        self.api = api
        self.device_id = device_id
        self.friendly_name = friendly_name
        self.user_lock = user_lock
        self._last_status = None

    async def enable(self):
        """Enable charging by unlocking user lock."""
        _LOGGER.debug(f"Attempting to enable charging for device {self.device_id} ({self.friendly_name})")
        success = await self.__runCommand('userUnlock')
        if success:
            _LOGGER.debug(f"Successfully enabled charging for device {self.device_id} ({self.friendly_name})")
            self.user_lock = True
        else:
            _LOGGER.warning(f"Failed to enable charging for device {self.device_id} ({self.friendly_name})")
        return success

    async def disable(self):
        """Disable charging by locking user lock."""
        _LOGGER.debug(f"Attempting to disable charging for device {self.device_id} ({self.friendly_name})")
        success = await self.__runCommand('userLock')
        if success:
            _LOGGER.debug(f"Successfully disabled charging for device {self.device_id} ({self.friendly_name})")
            self.user_lock = False
        else:
            _LOGGER.warning(f"Failed to disable charging for device {self.device_id} ({self.friendly_name})")
        return success

    async def __runCommand(self, function):
        url = const.GRAPHQL_URL
        body = {
            'operationName': 'runAEVCommand',
            'variables': { 'deviceId': self.device_id, 'functionName': function },
            'query': const.GRAPHQL_RUN_COMMAND_QUERY
        }

        _LOGGER.debug(f"Sending API command to {url}: {function} for device {self.device_id}")
        
        # Run blocking requests call in an executor to avoid blocking the event loop
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: requests.post(url, json=body, auth=BearerAuth(self.api.token))
            )
            
            status_code = response.status_code
            _LOGGER.debug(f"API command response status code: {status_code}")
            
            if status_code == 200:
                try:
                    response_json = response.json()
                    _LOGGER.debug(f"API command response: {response_json}")
                    
                    # Check if there are errors in the GraphQL response
                    if 'errors' in response_json:
                        _LOGGER.warning(f"GraphQL errors in response: {response_json['errors']}")
                        return False
                        
                    return True
                except Exception as json_err:
                    _LOGGER.warning(f"Error parsing JSON response: {json_err}")
                    return False
            else:
                _LOGGER.warning(f"API command failed with status code {status_code}: {response.text}")
                return False
                
        except Exception as err:
            _LOGGER.error(f"Error executing API command {function}: {err}")
            return False

    async def getDeviceStatus(self):
        """Get the real-time status of the device."""
        url = const.GRAPHQL_URL
        body = {
            'operationName': 'getDeviceStatusSimple',
            'variables': { 'id': self.device_id },
            'query': const.GRAPHQL_DEVICE_STATUS_QUERY
        }

        # Run blocking requests call in an executor to avoid blocking the event loop
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: requests.post(url, json=body, auth=BearerAuth(self.api.token))
        )

        if response.status_code != 200:
            return None
            
        response_body = response.json()
        if 'data' not in response_body or 'getDevice' not in response_body['data'] or 'deviceStatus' not in response_body['data']['getDevice']:
            return None
        
        # Store the last status for reference in the lock entity
        status = response_body['data']['getDevice']['deviceStatus']
        
        # Log changes to important status values
        log_changes = False
        if self._last_status and 'evseState' in status and 'evseState' in self._last_status:
            if status['evseState'] != self._last_status['evseState']:
                _LOGGER.info(f"Device {self.friendly_name}: EVSE state changed from {self._last_status['evseState']} to {status['evseState']}")
                log_changes = True
                
        if self._last_status and 'online' in status and 'online' in self._last_status:
            if status['online'] != self._last_status['online']:
                _LOGGER.info(f"Device {self.friendly_name}: Online state changed from {self._last_status['online']} to {status['online']}")
                log_changes = True
                
        if log_changes:
            _LOGGER.debug(f"Full status for {self.friendly_name}: {status}")
            
        self._last_status = status
        return status

    async def getLastCharge(self):
        url = const.GRAPHQL_URL
        body = {
            'operationName': 'getDeviceCalculatedChargeLogs',
            'variables': { 'id': self.device_id, 'offset': 0, 'limit': 1, 'minEnergy': 0.5 },
            'query': const.GRAPHQL_DEVICE_CHARGE_LOGS_QUERY
        }

        # Run blocking requests call in an executor to avoid blocking the event loop
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: requests.post(url, json=body, auth=BearerAuth(self.api.token))
        )

        if response.status_code != 200:
            return None
            
        response_body = response.json()
        device_logs = response_body['data']['getDevice']['deviceCalculatedChargeLogs']
        if len(device_logs) == 0:
            return None

        latest_log = device_logs[0]
        return {
            'duration': latest_log['duration'],
            'chargeCostTotal': latest_log['chargeCostTotal'],
            'chargeEnergyTotal': latest_log['chargeEnergyTotal'],
            'gridCostTotal': latest_log['gridCostTotal'],
            'gridEnergyTotal': latest_log['gridEnergyTotal'],
            'solarEnergyTotal': latest_log['solarEnergyTotal'],
            'solarCostTotal': latest_log['solarCostTotal'],
            'surplusUsedCostTotal': latest_log['surplusUsedCostTotal'],
            'surplusUsedEnergyTotal': latest_log['surplusUsedEnergyTotal']
        }