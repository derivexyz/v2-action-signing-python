import requests
from web3 import Web3
from decimal import Decimal
from websocket import create_connection
import uuid

from v2_action_signing import SignedAction, RFQQuoteDetails, RFQQuoteModuleData, utils


def main():

    #########################################
    # Get existing testnet subaccoount info #
    #########################################

    SMART_CONTRACT_WALLET_ADDRESS = "0x8772185a1516f0d61fC1c2524926BfC69F95d698"
    SESSION_KEY_PRIVATE_KEY = "0x2ae8be44db8a590d20bffbe3b6872df9b569147d3bf6801a35a28281a4816bbd"
    web3_client = Web3()
    session_key_wallet = web3_client.eth.account.from_key(SESSION_KEY_PRIVATE_KEY)

    #############################################
    # Protocol Constants from docs.lyra.finance #
    #############################################

    DOMAIN_SEPARATOR = "0x9bcf4dc06df5d8bf23af818d5716491b995020f377d3b7b64c29ed14e3dd1105"
    ACTION_TYPEHASH = "0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17"
    RFQ_MODULE_ADDRESS = "0x4E4DD8Be1e461913D9A5DBC4B830e67a8694ebCa"
    WEBSOCKET_URL = "wss://api-demo.lyra.finance/ws"

    ##########################
    # Get instrument details #
    ##########################

    response = requests.post(
        "https://api-demo.lyra.finance/public/get_instruments",
        json={
            "expired": False,
            "instrument_type": "option",
            "currency": "ETH",
        },
        headers={"accept": "application/json", "content-type": "application/json"},
    )

    live_instrument_ticker = response.json()["result"][0]  # choose first live instrument
    second_live_instrument_ticker = response.json()["result"][1]  # choose second live instrument

    #####################
    # Sign order action #
    #####################

    subaccount_id = 30769
    action = SignedAction(
        subaccount_id=subaccount_id,
        owner=SMART_CONTRACT_WALLET_ADDRESS,
        signer=session_key_wallet.address,
        signature_expiry_sec=utils.MAX_INT_32,
        nonce=utils.get_action_nonce(),
        module_address=RFQ_MODULE_ADDRESS,
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
        DOMAIN_SEPARATOR=DOMAIN_SEPARATOR,
        ACTION_TYPEHASH=ACTION_TYPEHASH,
    )

    action.sign(session_key_wallet.key)

    ############################
    # compare with debug route #
    ############################

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
            "signature_expiry_sec": utils.MAX_INT_32,
            "signature": action.signature,
            "signer": action.signer,
            "subaccount_id": subaccount_id,
        },
        headers={
            "accept": "application/json",
            "content-type": "application/json",
        },
    )
    results = response.json()["result"]

    assert "0x" + action.module_data.to_abi_encoded().hex() == results["encoded_data"]
    assert action._get_action_hash().hex() == results["action_hash"]
    assert action._to_typed_data_hash().hex() == results["typed_data_hash"]

    print("RFQ Quote signed correctly!")


if __name__ == "__main__":
    main()
