import asyncio
import requests
from . import const
from .device import KonnectDevice
from warrant.aws_srp import AWSSRP

class KonnectClient:
    email = None
    username = None
    password = None

    token = None
    tokenType = None
    tokenExpiresIn = None
    refreshToken = None

    def __init__(self, email, password):
        self.email = email
        self.password = password

    async def authenticate_user(self):
        # Before we can sign in, we need to determine the username. This is done
        # by making a request that for a given email, it will return the username
        # (if it exists.)
        self.username = await self.__fetchUsername()

        try:
            # Run the AWS SRP authentication in an executor to avoid blocking the event loop
            aws_response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.__authenticate_with_aws_srp
            )

            aws_result = aws_response['AuthenticationResult']
            self.token = aws_result['IdToken']
            self.tokenType = aws_result['TokenType']
            self.tokenExpiresIn = aws_result['ExpiresIn']
            self.refreshToken = aws_result['RefreshToken']
        except Exception as e:
            raise Exception(f'Failed to sign in: {str(e)}')

    def __authenticate_with_aws_srp(self):
        # This is executed in the executor pool
        aws_srp = AWSSRP(
            username = self.username,
            password = self.password,
            pool_id = 'eu-west-1_t5HV3bFjl',
            pool_region = 'eu-west-1',
            client_id = '23s0olnnniu5472ons0d9uoqt9')
        return aws_srp.authenticate_user()

    async def getDevices(self):
        self.__checkToken()
        devices = []

        url = const.API_DEVICES_URL
        
        # Run blocking requests call in an executor to avoid blocking the event loop
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: requests.get(url, headers={"Authorization": f"Bearer {self.token}"})
        )

        if response.status_code != 200:
            print('Status Code: ' + str(response.status_code))
            return devices

        response_body = response.json()

        # Log Devices
        print(response_body)

        for device in response_body['devices']:
            devices.append(KonnectDevice(
                api = self,
                device_id = device['id'],
                friendly_name = device['friendlyName'],
                user_lock = device['userLock']))

        return devices

    async def __fetchUsername(self):
        url = const.GRAPHQL_USER_MAP_URL
        body = { 'email': self.email }
        
        # Run blocking requests call in an executor to avoid blocking the event loop
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: requests.post(url, json=body)
        )

        if response.status_code != 200:
            raise Exception('Incorrect email address')

        # {'error': 'Pending user with email "x" not found'}
        # {'username': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:x'}
        response_body = response.json()
        if ('username' not in response_body):
            raise Exception('Incorrect email address')

        return response_body['username']

    def __checkToken(self):
        if self.token == None:
            raise Exception('Not signed in')