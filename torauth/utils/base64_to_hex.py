import base64


def base64_to_hex(base64str):
    return base64.b64decode(base64str).hex()
