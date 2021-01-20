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
        wallet_address: str,
        public_key: str,
        context: Any,
        retention_sec=3600
    ) -> str:
        '''
        Saves context and returns a QR code required for the authentication process
        :param public_key: user public key
        :param context: serializable context
        :param retention_sec: time limit in seconds as long as the QR code is valid
        :return: QR code encoded as base64 string
        '''
        rand = (
            await self.cfg.client.crypto.generate_random_bytes(
                ParamsOfGenerateRandomBytes(length=24)
            )
        ).bytes

        self.cache.add(
            wallet_address,
            public_key,
            retention_sec,
            rand,  # Base64 encoded
            context)
        return gen_qr_code(self.cfg.deep_link_url, rand)

    async def init(self, callback: Callable) -> None:
        '''
        Creates a subscription to the ROOT contract messages and start message processing
        :param callback: async function with signature (context: Any, result: bool)
        '''
        self.callback = callback
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
        self.is_subscribed = True

        self._task = asyncio.create_task(self._handle_messages(1))

    async def close(self) -> None:
        '''
        Remove subscription and stop ROOT contract message processing
        '''
        self.is_subscribed = False
        await self.cfg.client.net.unsubscribe(params=self._subscription)
        self._task.cancel()

    async def _handle_messages(self, period: int) -> None:
        '''
        This function periodically checks and process incoming messages.
        If the message contains a signed 'random', then the 'random' is compared with one from the cache,
        and a callback with the result of comparision is called.
        :param period: time interval for checking the message queue
        '''

        while self.is_subscribed:
            try:
                print("Checking...")

                obsolete_contexts = self.cache.clean_obsolete()
                for context in obsolete_contexts:
                    log.debug('Executing callback with obsolete context')
                    asyncio.create_task(self.callback(context, False))

                if len(self.messages) > 0:

                    _, (wallet_address, boc) = self.messages.popitem()

                    body = (
                        await self.cfg.client.boc.parse_message(params=ParamsOfParse(boc))
                    ).parsed['body']

                    signed_otp = (
                        await self.cfg.client.abi.decode_message_body(params=ParamsOfDecodeMessageBody(
                            abi=self.cfg.root_interface_abi,
                            body=body,
                            is_internal=True,
                        ))
                    ).value['signedOTP']

                    cached = self.cache.get(wallet_address)

                    if cached:
                        context = cached['context']

                        hash_of_initial_random = (await self.cfg.client.crypto.sha256(params=ParamsOfHash(
                            data=string_to_base64(cached['rand'])
                        ))).hash

                        signed = hex_to_base64(
                            signed_otp + hash_of_initial_random
                        )

                        hash_of_received_random = (await self.cfg.client.crypto.nacl_sign_open(
                            params=ParamsOfNaclSignOpen(
                                signed=signed,
                                public=cached['public_key']
                            )
                        )).unsigned

                        if hash_of_initial_random == base64_to_hex(hash_of_received_random):
                            log.debug('Check passed')
                            self.cache.remove(wallet_address)
                            asyncio.create_task(self.callback(context, True))

                        else:
                            log.debug('Randoms are NOT equal')
                            asyncio.create_task(self.callback(context, False))
                    else:
                        pass  # do nothing

                    await asyncio.sleep(0)
                else:
                    await asyncio.sleep(period)

            # We subscribed to all messages to the ROOT contract,
            # not them all are related to authorization, and
            # sometimes our validation code will fail
            except (KeyError, AttributeError, ValueError, TonException):
                pass
            except asyncio.CancelledError:
                log.debug('OK. Message handling is canceled')
            except:
                log.error('Unexpected error: {}'.format(sys.exc_info()[1]))
                raise
