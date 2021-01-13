import os
import asyncio
import logging
from unittest import IsolatedAsyncioTestCase

from . mocks.Surf import Surf
from torauth import Authenticator, Config

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))

config = Config()
auth = Authenticator(config)


class UserAuthFail(IsolatedAsyncioTestCase):
    ''' 
    This test:
    - creates a SURF user
    - Asks backend to generate QR code containing some random value
    - Signs received random value in the SURF
    - Recives a callback with a results of authentication

    In this test, we set a short retention time = 2 seconds,
    so the user authentication will be out of date before he sends the message.
    '''
    async def asyncSetUp(self):
        root_address = await auth.get_root_address()

        # Create a wallet for a test user
        self.surf = Surf(config, root_address)
        await self.surf.deploy_wallet()

        # Remember user pk, we need it to generate QR code
        self.user_public_key = await self.surf.get_public_key()

    async def test_success_confirmation(self):
        auth_completed = asyncio.Future()
        test_context = {'user': 'Ron'}

        async def on_auth_callback(context, result):
            auth_completed.set_result({'context': context, 'ok': result})

        # Initializing torauth with a callback function
        await auth.init(on_auth_callback)

        # Ask backend to register callback function and generate QR code,
        # which will be shown to the user
        #
        # param self.user_public_key: used to generate QR code
        # param context: Serializable object, that will be used as a callback parameter
        # param retention_sec: period of time while the QR code is valid
        base64_QR_code = await auth.start_authentication(
            self.user_public_key, context=test_context, retention_sec=2
        )

        # Pretend that a user has scanned a QR-code and been redirected to the Surf
        asyncio.create_task(self.surf.send_qr_code(base64_QR_code))

        result = await auth_completed
        self.assertEqual(result['context'], test_context)
        self.assertEqual(result['ok'], False)

    async def asyncTearDown(self):
        await auth.close()
