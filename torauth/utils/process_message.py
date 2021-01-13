from tonclient.errors import TonException
import os
import logging
import asyncio

log = logging.getLogger(__name__)

async def process_message(client, params):
    i = 1
    while True:
        try:
            log.debug('Processing message, try #{}'.format(i))
            await client.processing.process_message(params)
            break
        except TonException as err:
            i = i + 1
            log.debug('Ton error,{} \nTrying again...'.format(err))
            await asyncio.sleep(10)
