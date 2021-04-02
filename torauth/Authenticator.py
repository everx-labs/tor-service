import sys
import asyncio
import logging
from typing import Callable, Any

from tonclient.errors import TonException
from tonclient.types import ParamsOfGenerateRandomBytes, ParamsOfDecodeMessageBody, \
    ParamsOfParse, ParamsOfSubscribeCollection, ParamsOfNaclSignOpen, \
    KeyPair, DeploySet, Signer, SubscriptionResponseType, ParamsOfHash

from torauth.Cache import Cache
from torauth.Config import Config
from torauth.gen_qr_code import gen_qr_code
from torauth.utils import calc_address, hex_to_base64, base64_to_hex, string_to_base64

log = logging.getLogger(__name__)


class Authenticator:
    ''' Authenticating a site user providing his public_key as a TON blockchain user '''

    def __init__(self, config: Config = None):
        '''
        :param config: config object, initializing from env vars
        '''
        if config is None:
            config = Config()
        self.cfg = config
        self.messages = {}
        self.cache = Cache()
        self._callback = None
        self._subscription = None
        self._task = None
        self._is_subscribed = False

    async def get_root_address(self) -> str:
        '''
        Returns an address of the ROOT contract
        :return: str
        '''
        signer = Signer.Keys(
            KeyPair(public=self.cfg.root_public, secret=self.cfg.root_secret)
        )
        return await calc_address(
            client=self.cfg.client,
            abi=self.cfg.root_abi,
            signer=signer,
            deploy_set=DeploySet(tvc=self.cfg.root_tvc)
        )

    async def start_authentication(
        self,
        webhook_url: str,
        pin: str,
        context: Any,
        retention_sec=3600
    ) -> str:
        '''
        Saves context and returns a QR code required for the authentication process
        :param webhook_url: endpoint for POST request from Surf
        :param pin: pin code used when logged-in user wants to link Surf wallet
        :param context: serializable context
        :param retention_sec: time limit in seconds as long as the QR code is valid
        :return: QR code encoded as base64 string
        '''
        rand = (
            await self.cfg.client.crypto.generate_random_bytes(
                ParamsOfGenerateRandomBytes(length=24)
            )
        ).bytes

        seq = rand  # or uuid.uuid4().hex
        self.cache.add(
            seq=seq,
            webhook_url=webhook_url,
            pin=pin,
            retention_sec=retention_sec,
            rand=rand,
            context=context)

        return gen_qr_code(
            deep_link_url=self.cfg.deep_link_url,
            seq=seq,
            rand=rand,
            webhook_url=webhook_url)

    async def hook(self, json) -> None:
        if 'seq' in json:
            seq = json['seq']
            cached = self.cache.get(seq)
            if cached is not None:
                def exec_callback(**kwargs):
                    asyncio.create_task(self._callback(
                        context=cached['context'], **kwargs))

                try:
                    pin = cached['pin']
                    public_key = json['public_key']
                    wallet_address = json['wallet_address']
                    signed_message = json['signed_message']

                    hash_of_initial_random = (await self.cfg.client.crypto.sha256(params=ParamsOfHash(
                        data=string_to_base64(
                            cached['rand'] + ('' if pin is None else pin))
                    ))).hash

                    signed = hex_to_base64(
                        signed_message + hash_of_initial_random
                    )

                    hash_of_received_random = (await self.cfg.client.crypto.nacl_sign_open(
                        params=ParamsOfNaclSignOpen(
                            signed=signed,
                            public=public_key
                        )
                    )).unsigned

                    if hash_of_initial_random == base64_to_hex(hash_of_received_random):
                        log.debug('Check passed')
                        self.cache.remove(seq)
                        exec_callback(
                            public_key=public_key,
                            wallet_address=wallet_address,
                            result=True
                        )
                    else:
                        log.debug('Randoms are NOT equal')
                        exec_callback(result=False)

                except:
                    log.error(f'Check sign error: {sys.exc_info()[1]}')
                    exec_callback(result=False)

    async def init(self, callback: Callable) -> None:
        '''
        Creates a subscription to the ROOT contract messages and start message processing
        :param callback: async function with signature (context: Any, result: bool)
        '''
        self._callback = callback
        root_address = await self.get_root_address()

        def save_message(response_data, response_type, *args):
            if response_type == SubscriptionResponseType.OK:
                _id = response_data['result']['id']
                wallet_address = response_data['result']['src']
                boc = response_data['result']['boc']
                self.messages[_id] = (wallet_address, boc)

        self._subscription = await self.cfg.client.net.subscribe_collection(
            params=ParamsOfSubscribeCollection(
                collection='messages',
                result='src id boc',
                filter={'dst': {'eq': root_address}}
            ),
            callback=save_message
        )
        self._task = asyncio.create_task(self._handle_messages(1))
        self._is_subscribed = True

    async def close(self) -> None:
        '''
        Remove subscription and stop ROOT contract message processing
        '''
        if self._subscription is not None:
            await self.cfg.client.net.unsubscribe(params=self._subscription)
        if self._task is not None:
            self._task.cancel()

    async def _handle_messages(self, period: int) -> None:
        '''
        This function periodically checks and process incoming messages.
        If the message contains a signed 'random', then the 'random' is compared with one from the cache,
        and a callback with the result of comparision is called.
        :param period: time interval for checking the message queue
        '''

        while self._is_subscribed:
            try:
                log.debug("Checking...")
                obsolete_contexts = self.cache.clean_obsolete()
                for context in obsolete_contexts:
                    log.debug('Executing callback with obsolete context')
                    asyncio.create_task(self._callback(context, False))

                if len(self.messages) > 0:
                    # _, (wallet_address, boc) = self.messages.popitem()
                    # Next code temporary removed as unused
                    pass
                else:
                    await asyncio.sleep(period)

            # We subscribed to all messages to the ROOT contract,
            # not them all are related to authorization, and
            # sometimes our validation code will fail
            except (KeyError, AttributeError, ValueError, TonException):
                asyncio.sleep(0)
            except asyncio.CancelledError:
                log.debug('OK. Message handling is canceled')
                self._is_subscribed = False
            except:
                log.error(f'Unexpected error: {sys.exc_info()[1]}')
                raise
