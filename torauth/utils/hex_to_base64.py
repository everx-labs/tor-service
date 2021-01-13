import base64


def hex_to_base64(str):
    return base64.b64encode(bytes.fromhex(str)).decode()
