from tonclient.types import ParamsOfEncodeMessage

async def calc_address(client, abi, signer, deploy_set):
    msg = await client.abi.encode_message(params=ParamsOfEncodeMessage(
        abi=abi,
        signer=signer,
        deploy_set=deploy_set
    ))

    return msg.address
