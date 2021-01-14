# Authentication and authorization package for a website

## Prerequisites

Python 3.x (code was tested with Python 3.8.6)

Network connection: external public API (https://zxing.org) is used to decode QR code

## Implemented functionality

-   Ability to deploy Multisig wallet with one custodian in TON blockchain
-   Confirmation that the user of the website, who provided some public key actually owns it

To accomplish the latter task, the following steps are performed:

-   The user provides his public key

-   Backend generates QR code containing some "random string"

-   User scans this QR code and is redirected to Surf

-   The user signs received "random string" with his keys

-   Backend gets signed string and checks if it is equal to the generated one

-   Backend calls back with authentication result

## Installation

```
pip install --user -r requirements.txt
```

## Run test

```
python -m unittest -v tests/UserAuthSuccess.py
python -m unittest -v tests/UserAuthFail.py
```

## Example

```
from torauth import Authenticator, Config, deploy_wallet

config = Config()
auth = Authenticator(config)

# Define authentication callback
async def on_auth_callback(context: Any, result: bool):
    print('Authentication result is {}'.format(result))

# Initialize auth module by passing a callback function
await auth.init( on_auth_callback )

# if you need to change callback function, 
# call auth.close(), before re-initialization

async def authenticate_user(user_id):

    # get `wallet_address`, `public_key`, `secrect_key` from your store OR
    # create a new one. Remember to save return values
    wallet_address, public_key, secrect_key = await deploy_wallet(config)

    # Ask for QR code to start authentication procedure
    base64_qr_code = await auth.start_authentication(
        public_key = public_key,     #
        retention_sec = 600,         # The period of time this QR code is valid
        context = {"user_id": ....}  # Any serializable context. It will be
                                     # used as a parameter of the callback
    )

    # Show this code to the user so they can scan it

    # When the user completes the authentication procedure in Surf or
    # `retention_sec` period has passed, callback
    # `on_auth_callback(context, result)` will be executed
```
See: `tests/UserAuthSuccess.py`

### TODO

    - Implement exponential backoff in case of network errors
    - Rights management ...
