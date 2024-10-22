import pytest
from lyra_v2_action_signing import SignedAction, TradeModuleData
from lyra_v2_action_signing.utils import MAX_INT_32, get_action_nonce, sign_rest_auth_header
from decimal import Decimal
from web3 import Web3
import requests


def test_sign_order(
    domain_separator,
    action_typehash,
    module_addresses,
    live_instrument_ticker,
):

    #########################################
    # Get existing testnet subaccoount info #
    #########################################

    SMART_CONTRACT_WALLET_ADDRESS = "0x8772185a1516f0d61fC1c2524926BfC69F95d698"
    SESSION_KEY_PRIVATE_KEY = "0x2ae8be44db8a590d20bffbe3b6872df9b569147d3bf6801a35a28281a4816bbd"
    web3_client = Web3()
    session_key_wallet = web3_client.eth.account.from_key(SESSION_KEY_PRIVATE_KEY)

    #####################
    # Sign order action #
    #####################

    subaccount_id = 30769
    action = SignedAction(
        subaccount_id=subaccount_id,
        owner=SMART_CONTRACT_WALLET_ADDRESS,
        signer=session_key_wallet.address,
        signature_expiry_sec=MAX_INT_32,
        nonce=get_action_nonce(),
        module_address=module_addresses["trade"],
        module_data=TradeModuleData(
            asset_address=live_instrument_ticker["base_asset_address"],
            sub_id=int(live_instrument_ticker["base_asset_sub_id"]),
            limit_price=Decimal("100"),
            amount=Decimal("1"),
            max_fee=Decimal("1000"),
            recipient_id=subaccount_id,
            is_bid=True,
        ),
        DOMAIN_SEPARATOR=domain_separator,
        ACTION_TYPEHASH=action_typehash,
    )

    action.sign(session_key_wallet.key)

    assert action.signature is not None

    ############################
    # compare with debug route #
    ############################

    auth_headers = sign_rest_auth_header(web3_client, SMART_CONTRACT_WALLET_ADDRESS, SESSION_KEY_PRIVATE_KEY)
    response = requests.post(
        "https://api-demo.lyra.finance/private/order_debug",
        json={
            "instrument_name": live_instrument_ticker["instrument_name"],
            "direction": "buy",
            "order_type": "limit",
            "mmp": False,
            "time_in_force": "gtc",
            **action.to_json(),
        },
        headers={
            **auth_headers,
            "accept": "application/json",
            "content-type": "application/json",
        },
    )

    print(action._to_typed_data_hash().hex())
    results = response.json()["result"]

    assert ("0x" + action._get_action_hash().hex()) == results["action_hash"]
    assert ("0x" + action._to_typed_data_hash().hex()) == results["typed_data_hash"]
    assert "0x" + action.module_data.to_abi_encoded().hex() == results["encoded_data"]
