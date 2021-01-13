import os
import logging
from unittest import IsolatedAsyncioTestCase

from torauth import Config, deploy_root_contract

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))

config = Config()


class DeployRootContract(IsolatedAsyncioTestCase):
    async def test(self):
        await deploy_root_contract(config)
