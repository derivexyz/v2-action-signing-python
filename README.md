# v2-action-signing-python
Python package to sign the following on-chain self-custodial requests:

1. order
2. RFQ quote
3. RFQ execution
4. transfer positions


Although the below actions are supported by the SDK, we recommend you use the UX developer portal (https://docs.derive.xyz/docs/onboard-via-interface):

4. create subaccount
5. deposit
6. withdrawal
7. transfer collateral

⚠️ **Warning:** Note, the `owner` address and the `X-LyraWallet` is the Derive wallet address of the user. This is NOT your original EOA, but the smart contract wallet on the Derive Chain. To find it in the website go to Home -> Developers -> "Derive Wallet".

## Usage

1. Install package:
`pip install derive_action_signing`

2. Sign an order
```python
from web3 import Web3
from derive_action_signing import SignedAction, TradeModuleData, utils

session_key_wallet = Web3().eth.account.from_key("0x2ae8be44db8a590d20bffbe3b6872df9b569147d3bf6801a35a28281a4816bbd")

action = SignedAction(
    subaccount_id=30769,
    # The Derive wallet address (not "owner") of account. This is NOT your original EOA, but the smart contract wallet on the Derive Chain. To find it in the website go to Home -> Developers -> "Derive Wallet".
    owner=SMART_CONTRACT_WALLET_ADDRESS,
    signer=session_key_wallet.address,
    signature_expiry_sec=utils.MAX_INT_32,
    nonce=utils.get_action_nonce(),
    module_address=TRADE_MODULE_ADDRESS, # from Protocol Constants table in docs.lyra.finance
    module_data=TradeModuleData(
        asset=instrument_ticker["base_asset_address"],
        sub_id=int(instrument_ticker["base_asset_sub_id"]),
        limit_price=Decimal("100"),
        amount=Decimal("1"),
        max_fee=Decimal("1000"),
        recipient_id=30769,
        is_bid=True,
    ),
    DOMAIN_SEPARATOR=DOMAIN_SEPARATOR, # from Protocol Constants table in docs.derive.xyz
    ACTION_TYPEHASH=ACTION_TYPEHASH, # from Protocol Constants table in docs.derive.xyz
)

action.sign(session_key_wallet.key)
```

For full signing examples see `examples/` in https://github.com/derivexyz/v2-action-signing-python/tree/master/examples.

## Acknowledgements

Thank you 8baller for building a full Python client for the v2 API. Much of the signing logic in the repo was used to inform this package: https://github.com/8ball030/lyra_client

## Developers

1. Create venv and run `pip install -e .`, this reflects changes in package immediately in venv
2. Install dev related packages with `pip install -r requirements-dev.txt`
