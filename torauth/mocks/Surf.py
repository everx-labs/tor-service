import re
import os
import sys
import json
import logging
import asyncio
from functools import wraps, partial
import aiohttp
from tonclient.types import ParamsOfNaclSign, ParamsOfHash
from torauth.utils import string_to_base64, hex_to_base64
from . debot import debot

##
# This is a Surf mock working with real DeBot
# To decode QR code external public API is used
external_api = 'https://zxing.org/w/decode'
log = logging.getLogger(__name__)
debot_address = '0:a4543b20e0b169a7d3edb354d0aa45bc0ada23d357104ade368efde09099ec0e'

tmpfiles = './tmp/{}.keys'


def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, partial(func, *args, **kwargs))
    return run


async_debot = async_wrap(debot)


class Surf:

    def __init__(self, config, wallet_address, public, secret, callback_type='blockchain'):
        self.cfg = config
        self.public = public
        self.secret = secret
        self.wallet_address = wallet_address
        self.callback_type = callback_type

    async def sign(self, qr_code, pin):
        # Unfortunately, API sends the answer in html format only,
        # so we need to parse it
        async def parse_qr_code(params):
            async with aiohttp.ClientSession() as session:
                try:
                    # To decode QR code we use external public API
                    async with session.get(external_api, params=params) as response:
                        log.debug(f'Status: {response.status}')
                        if response.status == 200:
                            # Surf got `random` from QR code
                            html = await response.text()
                            (rand, seq, webhook_url) = self._extract_random(html)
                            return (rand, seq, webhook_url)
                        raise f'Http status {response.status}'
                except asyncio.CancelledError:
                    log.debug('OK. Surf canceled')
                except:
                    log.error(
                        f'Critical error in QR decoder service: {sys.exc_info()[1]}')
                    sys.exit(1)

        one_time_password, seq, webhook_url = await parse_qr_code({'u': f'data:image/png;base64,{qr_code}'})

        if self.callback_type == 'blockchain':
            keys_filename = os.path.join(
                os.path.dirname(__file__),
                tmpfiles.format(self.wallet_address)
            )
            with open(keys_filename, 'w') as outfile:
                json.dump({"public": self. public,
                           "secret": self.secret}, outfile)

            message_is_sent = False
            while not message_is_sent:
                message_is_sent = await async_debot(
                    debot_address,
                    self.wallet_address,
                    keys_filename,
                    one_time_password
                )
        else:
            # lets sign one_time_password + pin (maybe)
            message_hash = (await self.cfg.client.crypto.sha256(params=ParamsOfHash(
                data=string_to_base64(
                    one_time_password + ('' if pin is None else pin)
                )))).hash  # hex string

            signed_message = (await self.cfg.client.crypto.nacl_sign_detached(
                ParamsOfNaclSign(
                    unsigned=hex_to_base64(message_hash),
                    secret=self.secret + self.public
                )
            )).signature

            data = {
                "seq": seq,
                "signed_message": signed_message,
                "public_key": self.public,
                "wallet_address": self.wallet_address
            }
            async with aiohttp.ClientSession(json_serialize=json.dumps) as session:
                async with session.post(webhook_url, json=data) as response:
                    if response.status != 200:
                        log.error(
                            f'Local http server error: {sys.exc_info()[1]}')
                        sys.exit(1)

        log.debug('Message sent')

    def _extract_random(self, html):
        tokenized = re.split('<[^>]+>', html)
        res = list(filter(lambda x: self.cfg.deep_link_url in x, tokenized))
        value = res[0].split(self.cfg.deep_link_url)[-1].strip()
        return value.split(',')
