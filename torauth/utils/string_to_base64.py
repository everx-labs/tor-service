import base64


def string_to_base64(string):
    return base64.b64encode(string.encode('utf-8')).decode('utf-8')
