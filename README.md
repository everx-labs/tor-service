# Authentication and authorization package for a website

## Prerequisites

Python 3.x (code was tested with Python 3.8.6)

Network connection: external public API (https://zxing.org) is used to decode QR code


## Implemented functionality

- Confirmation that the user of the website, who provided some public key actually owns it on the TON network

To accomplish this task, the following steps are performed:

- The user provides his public key

- Backend generates some QR code containing "random string"

- User scans this QR code and is redirected to Surf

- The user signs a "random string" from the QR code with his keys

- Backend gets a random signed string and checks if it is equal to the generated one

- Backend calls back with authentication result


## Installation

```
pip install --user -r requirements.txt
```

## Run test

```
LOGLEVEL=DEBUG python -m unittest -v tests/UserAuthSuccess.py
LOGLEVEL=DEBUG python -m unittest -v tests/UserAuthFail.py
```

## Example

```
from torauth import Authenticator

auth = Authenticator()

async def on_auth_callback(context: Any, result: bool):
    print('Authentication result is {}'.format(result))

async def initialize_torauth():
    # Start listening to messages to the ROOT contract
    await auth.init( on_auth_callback )

async def authenticate_user(user_public_key, context):
    # Start authentication procedure by sending context
    base64_qr_code = await auth.start_authentication(
        user_public_key,
        context,
        retention_sec = 600
    )

    # Callback `on_auth_callback(context, result)` will be executed
    # when the user completes the authentication procedure,
    # or the `retention_sec` period has passed
```

### TODO

    - Implement exponential backoff in case of network errors
    - Rights management ...
