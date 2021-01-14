import logging
from torauth.utils import credit, calc_address, process_message
from tonclient.types import Abi, KeyPair, DeploySet, CallSet, \
    Signer, ParamsOfParse, ParamsOfEncodeMessage, ParamsOfProcessMessage
log = logging.getLogger(__name__)


async def deploy_root_contract(cfg) -> None:

    client = cfg.client
    wallet_abi = cfg.wallet_abi
    wallet_tvc = cfg.wallet_tvc
    root_abi = cfg.root_abi
    root_tvc = cfg.root_tvc
    root_initial_value = cfg.root_initial_value

    keys = await client.crypto.generate_random_sign_keys()

    signer = Signer.Keys(keys)

    wallet_msg = await client.abi.encode_message(params=ParamsOfEncodeMessage(
        abi=wallet_abi,
        signer=signer,
        deploy_set=DeploySet(tvc=wallet_tvc)
    ))

    result = await client.boc.parse_message(params=ParamsOfParse(boc=wallet_msg.message))
    wallet_code = result.parsed['code']

    call_set = CallSet(
        function_name='constructor',
        input={
            'name': 'bbbaaa',
            'symbol': 'beef',
            'root_public_key': '0x' + keys.public,
            'root_owner': '0x0',
            'wallet_code': wallet_code,
        },
    )

    address = await calc_address(
        client=client,
        abi=root_abi,
        signer=signer,
        deploy_set=DeploySet(tvc=root_tvc)
    )

    await credit(cfg, address, root_initial_value)

    log.info('Deploying contract to: {}'.format(address))

    await process_message(
        client=client,
        params=ParamsOfProcessMessage(
            message_encode_params=ParamsOfEncodeMessage(
                abi=root_abi,
                signer=signer,
                address=address,
                deploy_set=DeploySet(tvc=root_tvc),
                call_set=call_set
            ),
            send_events=False
        ))
    log.info(
        'Success!\n' +
        'Add these lines to the end of the .env file:\n' +
        f'ROOT_PUBLIC={keys.public}\n' +
        f'ROOT_SECRET={keys.secret}'
    )
