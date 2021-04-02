import logging
from tonclient.types import DeploySet, CallSet, Signer, ParamsOfProcessMessage, ParamsOfEncodeMessage
from torauth import Config
from torauth.utils import credit, calc_address, process_message
log = logging.getLogger(__name__)


async def deploy_wallet(cfg: Config) -> (str, str, str):
    ''' This function deploys multisig wallet with one custodian
    :param cfg: Configuration object, containing contract ABI and code
    :return Tuple: (wallet_address, public_key, secret_key)
    '''
    keys = await cfg.client.crypto.generate_random_sign_keys()
    signer = Signer.Keys(keys)

    address = await calc_address(
        client=cfg.client,
        abi=cfg.multisig_abi,
        signer=signer,
        deploy_set=DeploySet(tvc=cfg.multisig_tvc)
    )

    await credit(cfg, address, cfg.multisig_initial_value)

    log.info(f'Deploying contract to {address}')

    await process_message(
        client=cfg.client,
        params=ParamsOfProcessMessage(
            message_encode_params=ParamsOfEncodeMessage(
                abi=cfg.multisig_abi,
                signer=signer,
                address=address,
                deploy_set=DeploySet(tvc=cfg.multisig_tvc),
                call_set=CallSet(
                    function_name='constructor',
                    input={
                        'owners': ['0x' + keys.public],
                        'reqConfirms': 1
                    },
                )
            ),
            send_events=False
        ))
    return (address, keys.public, keys.secret)
