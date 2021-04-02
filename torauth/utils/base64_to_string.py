import base64


def base64_to_string(encoded_str):
    return str(base64.b64decode(encoded_str), "utf-8")
