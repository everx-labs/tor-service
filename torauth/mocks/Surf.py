import re
import os
import sys
import json
import logging
import asyncio
from functools import wraps, partial
import aiohttp
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
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run


async_debot = async_wrap(debot)


class Surf:

    def __init__(self, config, wallet_address, public, secret):
        self.cfg = config
        self.public = public
        self.secret = secret
        self.wallet_address = wallet_address

    async def sign(self, qr_code):
        async with aiohttp.ClientSession() as session:
            try:
              # To decode QR code we use external public API
                params = {'u': 'data:image/png;base64,{}'.format(qr_code)}
                async with session.get(external_api, params=params) as response:
                    log.debug('Status: {}'.format(response.status))
                    if response.status == 200:
                        # Surf got `random` from QR code
                        html = await response.text()
                        one_time_password = self._extract_random(html)

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

                        log.debug('Message sent!')
                    else:
                        raise 'Http status {}'.format(response.status)
            except asyncio.CancelledError:
                log.debug('OK. Surf canceled')
            except:
                log.error('Critical error in QR decoder service: {}'.format(
                    sys.exc_info()[1]))
                sys.exit(1)

    # Unfortunately, API sends the answer in html format only,
    # so we need to parse it

    def _extract_random(self, html):
        tokenized = re.split('<[^>]+>', html)
        res = list(filter(lambda x: self.cfg.deep_link_url in x, tokenized))
        random = res[0].split(self.cfg.deep_link_url)[-1].strip()
        log.debug('Extracted from QR code random: {}'.format(random))
        return random
