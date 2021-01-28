import os
import asyncio
import logging
from unittest import IsolatedAsyncioTestCase

from . mocks.Surf import Surf
from torauth import Authenticator, Config, deploy_wallet

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))

config = Config()
auth = Authenticator(config)


class UserAuthFail(IsolatedAsyncioTestCase):
    '''
    This test has equal to UserAuthSuccess, except 
    that the retention time is set to be very short. 
    '''
    async def test_success_confirmation(self):

        # Create a wallet for a test user
        logging.info("Creating a new wallet for the user")
        (wallet_address, public_key, secret_key) = await deploy_wallet(config)
        logging.info("OK. wallet created")

        loop = asyncio.get_running_loop()
        auth_completed =  loop.create_future()
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
            retention_sec=2)

        logging.info("Got base64 QR code: {}.....truncated".format(
            base64_qr_code[0:25]))

        # Tune Surf instance
        surf = Surf(config, wallet_address, public_key, secret_key)
        # and send QR code to Surf. Encoded inside QR code `random string` will be signed
        task = asyncio.create_task(surf.sign(base64_qr_code))
        logging.info(
            "Pretend that QR code was shown and user was redirected to the Surf")

        result = await auth_completed
        task.cancel()
        logging.info("Authentication result is: {}".format(result['ok']))
        self.assertEqual(result['context'], test_context)
        self.assertEqual(result['ok'], False)

    async def asyncTearDown(self):
        await auth.close()
