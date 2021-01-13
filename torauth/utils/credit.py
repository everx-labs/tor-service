from tonclient.types import Signer, CallSet, ParamsOfEncodeMessage, ParamsOfProcessMessage
import os
import logging

from . process_message import process_message

log = logging.getLogger(__name__)


def credit(cfg, address, value):

    log.debug('Sending {} to {}'.format(value, address))

    return process_message(
        client=cfg.client,
        params=ParamsOfProcessMessage(
            message_encode_params=ParamsOfEncodeMessage(
                abi=cfg.giver_abi,
                signer=Signer.Keys(cfg.giver_keys),
                address=cfg.giver_address,
                call_set=CallSet(
                    function_name='sendTransaction',
                    input={'dest': address, 'value': value, 'bounce': False}
                )
            ), send_events=False
        ))
