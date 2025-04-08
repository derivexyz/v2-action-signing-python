import requests
import json
from web3 import Web3
from decimal import Decimal
from typing import List

from derive_action_signing import SignedAction, RFQQuoteDetails, RFQQuoteModuleData, utils


def main():
    # NOTE: before quoting RFQ, reach out to Lyra Exchange to be approved for RFQ quoting

    ########################################
    # Get existing testnet subaccount info #
    ########################################

    SMART_CONTRACT_WALLET_ADDRESS = "0x8772185a1516f0d61fC1c2524926BfC69F95d698"
    SESSION_KEY_PRIVATE_KEY = "0x2ae8be44db8a590d20bffbe3b6872df9b569147d3bf6801a35a28281a4816bbd"
    web3_client = Web3()
    session_key_wallet = web3_client.eth.account.from_key(SESSION_KEY_PRIVATE_KEY)
    SUBACCOUNT_ID = 30769

    #############################################
    # Protocol Constants from docs.lyra.finance #
    #############################################

    DOMAIN_SEPARATOR = "0x9bcf4dc06df5d8bf23af818d5716491b995020f377d3b7b64c29ed14e3dd1105"
    ACTION_TYPEHASH = "0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17"
    RFQ_MODULE_ADDRESS = "0x4E4DD8Be1e461913D9A5DBC4B830e67a8694ebCa"

    #############
    # Poll RFQs #
    #############

    # can also use {wallet}.rfqs channel to listen for RFQs (same response format)
    response = requests.post(
        "https://api-demo.lyra.finance/private/poll_rfqs",
        json={
            "subaccount_id": SUBACCOUNT_ID,
            "status": "open",
        },
        headers={
            **utils.sign_rest_auth_header(web3_client, SMART_CONTRACT_WALLET_ADDRESS, SESSION_KEY_PRIVATE_KEY),
            "accept": "application/json",
            "content-type": "application/json",
        },
    )

    try:
        rfq = response.json()["result"]["rfqs"][0]
    except IndexError:
        print("No open RFQs")
        return

    #####################
    # Sign quote action #
    #####################

    global_direction = "sell"
    rfq_legs: List[RFQQuoteDetails] = []
    for leg in rfq["legs"]:
        instrument_ticker = requests.post(
            "https://api-demo.lyra.finance/public/get_instrument",
            json={
                "instrument_name": leg["instrument_name"],
            },
            headers={"accept": "application/json", "content-type": "application/json"},
        ).json()["result"]

        rfq_legs.append(
            RFQQuoteDetails(
                instrument_name=instrument_ticker["instrument_name"],
                direction=leg["direction"],
                asset_address=instrument_ticker["base_asset_address"],
                sub_id=int(instrument_ticker["base_asset_sub_id"]),
                price=Decimal("100"),  # REPLACE WITH YOUR QUOTE
                amount=Decimal(leg["amount"]),
            )
        )

    action = SignedAction(
        subaccount_id=SUBACCOUNT_ID,
        owner=SMART_CONTRACT_WALLET_ADDRESS,
        signer=session_key_wallet.address,
        signature_expiry_sec=utils.MAX_INT_32,
        nonce=utils.get_action_nonce(),
        module_address=RFQ_MODULE_ADDRESS,
        module_data=RFQQuoteModuleData(
            global_direction=global_direction,
            max_fee=Decimal("123"),
            legs=rfq_legs,
        ),
        DOMAIN_SEPARATOR=DOMAIN_SEPARATOR,
        ACTION_TYPEHASH=ACTION_TYPEHASH,
    )

    action.sign(session_key_wallet.key)

    ##############
    # Send Quote #
    ##############

    response = requests.post(
        "https://api-demo.lyra.finance/private/send_quote",
        json={
            **action.to_json(),
            "label": "",
            "mmp": False,
            "rfq_id": rfq["rfq_id"],
        },
        headers={
            **utils.sign_rest_auth_header(web3_client, SMART_CONTRACT_WALLET_ADDRESS, SESSION_KEY_PRIVATE_KEY),
            "accept": "application/json",
            "content-type": "application/json",
        },
    )
    print("Sent Quote!")
    print(json.dumps(response.json(), indent=4))


if __name__ == "__main__":
    main()
