import pytest
from v2_action_signing import SignedAction, RFQQuoteModuleData, RFQQuoteDetails
from eth_account.signers.base import BaseAccount
from v2_action_signing.utils import MAX_INT_32, get_action_nonce, sign_auth_header
from decimal import Decimal
from web3 import Web3
import requests
import uuid


def test_sign_rfq_quote(
    domain_separator, action_typehash, module_addresses, live_instrument_ticker, second_live_instrument_ticker
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
        module_address=module_addresses["rfq"],
        module_data=RFQQuoteModuleData(
            max_fee=Decimal("1000"),
            trades=[
                RFQQuoteDetails(
                    asset=live_instrument_ticker["base_asset_address"],
                    sub_id=int(live_instrument_ticker["base_asset_sub_id"]),
                    price=Decimal("50"),
                    amount=Decimal("1"),
                ),
                RFQQuoteDetails(
                    asset=second_live_instrument_ticker["base_asset_address"],
                    sub_id=int(second_live_instrument_ticker["base_asset_sub_id"]),
                    price=Decimal("100"),
                    amount=Decimal("2"),
                ),
            ],
        ),
        DOMAIN_SEPARATOR=domain_separator,
        ACTION_TYPEHASH=action_typehash,
    )

    action.sign(session_key_wallet.key)

    assert action.signature is not None

    ############################
    # compare with debug route #
    ############################

    auth_headers = sign_auth_header(web3_client, SMART_CONTRACT_WALLET_ADDRESS, SESSION_KEY_PRIVATE_KEY)
    response = requests.post(
        "https://api-demo.lyra.finance/public/send_quote_debug",
        json={
            "direction": "buy",
            "label": "",
            "legs": [
                {
                    "amount": str(action.module_data.trades[0].amount),
                    "direction": "buy",
                    "instrument_name": live_instrument_ticker["instrument_name"],
                    "price": str(action.module_data.trades[0].price),
                },
                {
                    "amount": str(action.module_data.trades[1].amount),
                    "direction": "buy",
                    "instrument_name": second_live_instrument_ticker["instrument_name"],
                    "price": str(action.module_data.trades[1].price),
                },
            ],
            "max_fee": str(action.module_data.max_fee),
            "mmp": False,
            "nonce": action.nonce,
            "rfq_id": str(uuid.uuid4()),  # random rfq_id
            "signature_expiry_sec": MAX_INT_32,
            "signature": action.signature,
            "signer": action.signer,
            "subaccount_id": subaccount_id,
        },
        headers={
            "accept": "application/json",
            "content-type": "application/json",
        },
    )
    print(response.json())
    results = response.json()["result"]

    assert "0x" + action.module_data.to_abi_encoded().hex() == results["encoded_data"]
    assert action._get_action_hash().hex() == results["action_hash"]
    assert action._to_typed_data_hash().hex() == results["typed_data_hash"]
