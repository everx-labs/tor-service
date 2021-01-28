import os
import re
import base64
import logging
from dotenv import load_dotenv
from tonclient.client import TonClient
from tonclient.types import Abi, KeyPair, ClientConfig

log = logging.getLogger(__name__)


def onlydigits(string):
    return re.sub('[^0-9]', '', string)


def get_var(name):
    # All variables MUST be set
    value = os.getenv(name)
    log.debug('{} = {}'.format(name, value))
    if value is None:
        raise TypeError('Variable not set {}'.format(name))
    return value


def fullPath(fname):
    return os.path.join(os.path.dirname(__file__), get_var(fname))


class Config:

    ''' Authentificator configuration '''

    def __init__(self, filename=None):
        if filename is None:
            filename = os.path.join(os.path.dirname(__file__), 'env.default')

        self._from_file(filename)

    def _from_file(self, path):
        if os.path.isfile(path) == False:
            log.debug('File "{}" not exists, but maybe that\'s OK'.format(path))

        load_dotenv(path)
        self.root_abi = Abi.from_path(fullPath('ROOT_ABI'))
        self.wallet_abi = Abi.from_path(fullPath('WALLET_ABI'))
        self.giver_abi = Abi.from_path(fullPath('GIVER_ABI'))
        self.multisig_abi = Abi.from_path(fullPath('MULTISIG_ABI'))
        self.root_interface_abi = Abi.from_path(fullPath('ROOT_INTERFACE_ABI'))

        with open(fullPath('WALLET_TVC'), 'rb') as fp:
            self.wallet_tvc = base64.b64encode(fp.read()).decode()

        with open(fullPath('ROOT_TVC'), 'rb') as fp:
            self.root_tvc = base64.b64encode(fp.read()).decode()

        with open(fullPath('GIVER_TVC'), 'rb') as fp:
            self.giver_tvc = base64.b64encode(fp.read()).decode()

        with open(fullPath('MULTISIG_TVC'), 'rb') as fp:
            self.multisig_tvc = base64.b64encode(fp.read()).decode()

        client_config = ClientConfig()
        client_config.network.server_address = get_var('TON_SERVER_ADDRESS')

        self.client = TonClient(
            config=client_config,  is_core_async=True, is_async=True)

        self.giver_keys = KeyPair(
            public=get_var('GIVER_PUBLIC'),
            secret=get_var('GIVER_SECRET')
        )

        self.giver_address = get_var('GIVER_ADDRESS')

        self.root_public = get_var('ROOT_PUBLIC')
        self.root_secret = get_var('ROOT_SECRET')
        self.root_initial_value = onlydigits(get_var('ROOT_INITIAL_VALUE'))

        self.multisig_initial_value = onlydigits(
            get_var('MULTISIG_INITIAL_VALUE')
        )

        self.deep_link_url = get_var('DEEP_LINK_URL')
