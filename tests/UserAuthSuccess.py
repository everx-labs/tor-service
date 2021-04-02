import os
import asyncio
import logging
from unittest import IsolatedAsyncioTestCase
from aiohttp import web

from torauth import Authenticator, Config, deploy_wallet, Surf

PIN = '4352'
WEBHOOK_URL = 'http://localhost:8080/test'

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))

config = Config()
auth = Authenticator(config)


async def hook_handler(request):
    data = await request.json()
    await auth.hook(data)
    return web.Response(text="OK")


class UserAuthSuccess(IsolatedAsyncioTestCase):
    '''
    This test:
    - creates a SURF user
    - Asks backend to generate QR code containing some random value
    - Signs received random value in the SURF
    - Recives a callback with a results of authentication
    '''
    async def test_success_confirmation(self):

        server = web.Server(hook_handler)
        runner = web.ServerRunner(server)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()

        # Create a wallet for a test user
        logging.info("Creating a new wallet for the user")
        (wallet_address, public_key, secret_key) = await deploy_wallet(config)
        logging.info("OK. wallet created")

        loop = asyncio.get_running_loop()
        auth_completed = loop.create_future()
        test_context = {'user': 'Ron'}

        async def on_auth_callback(
                context: str, result: bool,  public_key: str = None, wallet_address: str = None):
            auth_completed.set_result({
                'context': context,
                'public_key': public_key,
                'wallet_address': wallet_address,
                'ok': result
            })

        # Initializing torauth with a callback function
        await auth.init(on_auth_callback)

        # Ask backend to register callback function and generate QR code,
        # which will be shown to the user
        #
        # param webhook_url: endpoint for POST request from Surf
        # param pin: pin code used when logged-in user wants to link Surf wallet
        # param context: Serializable object, that will be used as a callback parameter
        # param retention_sec: period of time while the QR code is valid
        base64_qr_code = await auth.start_authentication(
            webhook_url=WEBHOOK_URL,
            pin=PIN,
            context=test_context,
            retention_sec=18000)

        logging.info(
            f'Got base64 QR code: {base64_qr_code[0:25]}.....truncated')

        # Tune Surf instance
        surf = Surf(
            config, wallet_address, public_key, secret_key, callback_type='webhook'
        )
        # and send QR code to Surf. Encoded inside QR code `random string` will be signed
        asyncio.create_task(surf.sign(base64_qr_code, PIN))
        logging.info(
            "Pretend that QR code was shown and user was redirected to Surf")

        result = await auth_completed
        logging.info(f'Authentication result is: {result["ok"]}')
        self.assertEqual(result['context'], test_context)
        self.assertEqual(result['public_key'], public_key)
        self.assertEqual(result['wallet_address'], wallet_address)
        self.assertEqual(result['ok'], True)

    async def asyncTearDown(self):
        await auth.close()
