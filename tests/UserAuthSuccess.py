import os
import asyncio
import logging
from unittest import IsolatedAsyncioTestCase

from torauth import Authenticator, Config, deploy_wallet
from . mocks.Surf import Surf

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))

config = Config()
auth = Authenticator(config)


class UserAuthSuccess(IsolatedAsyncioTestCase):
    '''
    This test:
    - creates a SURF user
    - Asks backend to generate QR code containing some random value
    - Signs received random value in the SURF
    - Recives a callback with a results of authentication
    '''
    async def test_success_confirmation(self):

        # Create a wallet for a test user
        logging.info("Creating a new wallet for the user")
        (wallet_address, public_key, secret_key) = await deploy_wallet(config)
        logging.info("OK. wallet created")

        auth_completed = asyncio.Future()
        test_context = {'user': 'Ron'}

        async def on_auth_callback(context, result):
            auth_completed.set_result({'context': context, 'ok': result})

        # Initializing torauth with a callback function
        await auth.init(on_auth_callback)

        # Ask backend to register callback function and generate QR code,
        # which will be shown to the user
        #
        # param public_key: is used to generate QR code
        # param context: Serializable object, that will be used as a callback parameter
        # param retention_sec: period of time while the QR code is valid
        base64_qr_code = await auth.start_authentication(
            wallet_address,
            public_key,
            context=test_context,
            retention_sec=18000)

        logging.info("Got base64 QR code: {}.....truncated".format(
            base64_qr_code[0:25]))

        # Tune Surf instance
        surf = Surf(config, wallet_address, public_key, secret_key)
        # and send QR code to Surf. Encoded inside QR code `random string` will be signed
        asyncio.create_task(surf.sign(base64_qr_code))
        logging.info(
            "Pretend that QR code was shown and user was redirected to the Surf")

        result = await auth_completed
        logging.info("Authentication result is: {}".format(result['ok']))
        self.assertEqual(result['context'], test_context)
        self.assertEqual(result['ok'], True)

    async def asyncTearDown(self):
        await auth.close()
