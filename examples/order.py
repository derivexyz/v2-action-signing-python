import requests
from web3 import Web3
from decimal import Decimal
from websocket import create_connection
import json

from v2_action_signing import SignedAction, TradeModuleData, utils


def main():

    #####################################
    # Setup existing wallet and account #
    #####################################
    # Below account, subaccount, session key setup in advance via UX
    # Refer to docs.lyra.finance for creating account / depositing / creating session key via UX

    SMART_CONTRACT_WALLET_ADDRESS = "0x8772185a1516f0d61fC1c2524926BfC69F95d698"
    SESSION_KEY_PRIVATE_KEY = "0x2ae8be44db8a590d20bffbe3b6872df9b569147d3bf6801a35a28281a4816bbd"
    SUBACCOUNT_ID = 30769

    web3_client = Web3()
    session_key_wallet = web3_client.eth.account.from_key(SESSION_KEY_PRIVATE_KEY)

    #############################################
    # Protocol Constants from docs.lyra.finance #
    #############################################

    DOMAIN_SEPARATOR = "0x9bcf4dc06df5d8bf23af818d5716491b995020f377d3b7b64c29ed14e3dd1105"
    ACTION_TYPEHASH = "0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17"
    TRADE_MODULE_ADDRESS = "0x87F2863866D85E3192a35A73b388BD625D83f2be"
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

    instrument_ticker = response.json()["result"][0]  # choose first live instrument

    ##########################
    # Create Action and Sign #
    ##########################

    action = SignedAction(
        subaccount_id=SUBACCOUNT_ID,
        owner=SMART_CONTRACT_WALLET_ADDRESS,
        signer=session_key_wallet.address,
        signature_expiry_sec=utils.MAX_INT_32,
        nonce=utils.get_action_nonce(),
        module_address=TRADE_MODULE_ADDRESS,
        module_data=TradeModuleData(
            asset=instrument_ticker["base_asset_address"],
            sub_id=int(instrument_ticker["base_asset_sub_id"]),
            limit_price=Decimal("100"),
            amount=Decimal("1"),
            max_fee=Decimal("1000"),
            recipient_id=SUBACCOUNT_ID,
            is_bid=True,
        ),
        DOMAIN_SEPARATOR=DOMAIN_SEPARATOR,
        ACTION_TYPEHASH=ACTION_TYPEHASH,
    )

    action.sign(session_key_wallet.key)

    ########################
    # Login and send order #
    ########################

    ws = create_connection(WEBSOCKET_URL)
    id = str(utils.utc_now_ms())
    ws.send(
        json.dumps(
            {
                "method": "public/login",
                "params": utils.sign_auth_header(web3_client, SMART_CONTRACT_WALLET_ADDRESS, SESSION_KEY_PRIVATE_KEY),
                "id": id,
            }
        )
    )
    while True:
        message = json.loads(ws.recv())
        if message["id"] == id:
            if "result" not in message:
                raise Exception(f"Unable to login {message}")
            break

    # send order
    id = str(utils.utc_now_ms())
    ws.send(
        json.dumps(
            {
                "method": "private/order",
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
                print("Got order response", message["result"]["order"])
                print("Order signing and submission successful!")
                break
            except KeyError as error:
                print(message)
                raise Exception(f"Unable to submit order {message}") from error


if __name__ == "__main__":
    main()
