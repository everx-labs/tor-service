# Authentication and authorization package for a website

## Prerequisites

Python 3.x (code was tested with Python 3.8.6)

Network connection: external public API (https://zxing.org) is used to decode QR code

## Implemented functionality

-   Ability to deploy Multisig wallet with one custodian in TON blockchain
-   Signing in / Signing up using Surf wallet
-   Binding Surf wallet by an logged-in user

To complete the last two tasks, the following steps are performed:

-   Backend generates QR code containing some "random string"

-   The user is shown the QR code and (in the case of binding Surf wallet) PIN code

-   User scans this QR code and is redirected to Surf

-   The user inputs PIN (in the case of binding Surf wallet)

-   The user signs received "random string" with his keys

-   Backend gets signed string and checks if it is equal to the generated one

-   Backend calls back with authentication result, user wallet address and public key

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
import asyncio
from tests.mocks.Surf import Surf
from torauth import Authenticator, Config, deploy_wallet

config = Config()
auth = Authenticator(config)

# Define authentication callback
async def on_auth_callback(
                context: str, result: bool,  public_key: str = None, wallet_address: str = None):
    print(f'Authentication result is {result}') # Here we here all needed user data


# Initialize auth module by passing a callback function
await auth.init(on_auth_callback)

# if you need to change callback function,
# call auth.close(), before re-initialization

async def authenticate_user(user_id):

    # Ask for QR code to start authentication procedure
    base64_qr_code = await auth.start_authentication(
        webhook_url=WEBHOOK_URL,     # Endpoint where Surf returns signed data
        pin=PIN,                     # Used when logged-in user wants to bind Surf wallet
        retention_sec = 600,         # The period of time this QR code is valid
        context = {"user_id": ....}  # Any serializable context. It will be
                                     # used as a parameter of the callback
    )

    # Show this code to the user so they can scan it,
    # If the logged-in user wants to bind the Surf wallet, additionally show him the PIN code
    #
    # For automated testing we using Surf mock 
    surf = Surf(config, wallet_address, public_key, secret_key, callback_type='webhook')
    task = asyncio.create_task(surf.sign(base64_qr_code, PIN))

    # When the user completes the authentication procedure in Surf or
    # `retention_sec` period has passed, will be executed callback:
    # `on_auth_callback(context, result, public_key, wallet_address:)` 
```

You can find a real example here: `tests/UserAuthSuccess.py`

### TODO

    - Implement exponential backoff in case of network errors
    - Rights management ...
