import os
import logging
from unittest import IsolatedAsyncioTestCase

from torauth import Config, deploy_wallet

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))

config = Config()


class DeployWallet(IsolatedAsyncioTestCase):
    async def test(self):
        address, public, secret = await deploy_wallet(config)
        logging.debug('Wallet address: {}, public_key: {}, secret_key: {}'.format(
            address, public, secret)
        )
