from functools import wraps, partial
import asyncio
import os
import logging
from unittest import IsolatedAsyncioTestCase

from . mocks.debot import debot

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))

debot_address = '0:a4543b20e0b169a7d3edb354d0aa45bc0ada23d357104ade368efde09099ec0e'
wallet_address = "0:1a9af5ad556ad1d889a6963870fc46ccafaeb2382110a5f5c80730964408ce1f"
one_time_password = '1111'
keys_filename = os.path.join(
    os.path.dirname(__file__),
    'test_keys.txt'
)


def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run


cb = async_wrap(debot)


class Debot(IsolatedAsyncioTestCase):
    async def test_send_message(self):
        result = await cb(debot_address, wallet_address, keys_filename, one_time_password)
        print(result)
        self.assertEqual(result, True)
