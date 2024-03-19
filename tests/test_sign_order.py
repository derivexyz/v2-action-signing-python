import pytest
from v2_action_signing import SignedAction, TradeModuleData
from eth_account.signers.base import BaseAccount
from v2_action_signing.utils import MAX_INT_32, get_action_nonce
from decimal import Decimal

# Uses Testnet for all testing

###############################################################################
# Constants taken from https://docs.lyra.finance/reference/protocol-constants #
###############################################################################

# strategy:
# 1. test: create one real test account for order debug.
# 2. test: all other routes with debug.
# 3. example: scripts for each route and create real accounts there.


def test_sign_order(
    random_wallet: BaseAccount,
    random_session_key: BaseAccount,
    domain_separator,
    action_typehash,
    module_addresses,
    random_live_instrument_ticker,
):

    ############################################
    # Get sub_id and asset address from ticker #
    ############################################

    subaccount_id = 1
    action = SignedAction(
        subaccount_id=subaccount_id,
        owner=random_wallet.address,
        signer=random_session_key.address,
        signature_expiry_sec=MAX_INT_32,
        nonce=get_action_nonce(),
        module_address=module_addresses["trade"],
        module_data=TradeModuleData(
            asset=random_live_instrument_ticker["base_asset_address"],
            sub_id=int(random_live_instrument_ticker["base_asset_sub_id"]),
            limit_price=Decimal("100"),
            desired_amount=Decimal("1"),
            worst_fee=Decimal("1000"),
            recipient_id=subaccount_id,
            is_bid=True,
        ),
        DOMAIN_SEPARATOR=domain_separator,
        ACTION_TYPEHASH=action_typehash,
    )

    action.sign(random_session_key.key)

    assert action.signature is not None

    # compare with debug route

    id = str(utils.utc_now_ms())
    print("encoded data", action.module_data.to_abi_encoded().hex())
    print("action_hash", action._get_action_hash().hex())
    print("typed_data_hash", action._to_typed_data_hash().hex())
    ws.send(
        json.dumps(
            {
                "method": "private/order_debug",
                "params": {
                    "instrument_name": instrument_ticker["instrument_name"],
                    "subaccount_id": SUBACCOUNT_ID,
                    "direction": "buy",
                    "limit_price": str(action.module_data.limit_price),
                    "amount": str(action.module_data.amount),
                    "signature_expiry_sec": action.signature_expiry_sec,
                    "max_fee": str(action.module_data.max_fee),
                    "nonce": action.nonce,
                    "signer": action.signer,
                    "order_type": "limit",
                    "mmp": False,
                    "time_in_force": "gtc",
                    "signature": action.signature,
                },
                "id": id,
            }
        )
    )
    while True:
        message = json.loads(ws.recv())
        if message["id"] == id:
            try:
                print(message["result"])
            except KeyError as error:
                print(message)
                raise Exception(f"Unable to submit order {message}") from error
