import json
import requests
from web3 import Web3
from decimal import Decimal
import time
from lyra_v2_action_signing import SignedAction, RFQQuoteDetails, RFQExecuteModuleData, utils


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

    ###################################
    # Get two random live instruments #
    ###################################

    url = "https://api-demo.lyra.finance/public/get_instruments"
    payload = {
        "expired": False,
        "instrument_type": "option",
        "currency": "ETH",
    }
    response = requests.post(
        url, json=payload, headers={"accept": "application/json", "content-type": "application/json"}
    )

    first_instrument = response.json()["result"][0]
    second_instrument = response.json()["result"][1]

    #############
    # Send RFQs #
    #############

    rfq_module_data = RFQExecuteModuleData(
        quote_direction="buy",  # NOTE: this direction MUST match the direction of the received quote
        max_fee=Decimal("1000"),
        legs=[
            RFQQuoteDetails(
                instrument_name=first_instrument["instrument_name"],
                direction="buy",
                asset_address=first_instrument["base_asset_address"],
                sub_id=int(first_instrument["base_asset_sub_id"]),
                price=Decimal("0"),  # will be set when quote is returned
                amount=Decimal("1"),
            ),
            RFQQuoteDetails(
                instrument_name=second_instrument["instrument_name"],
                direction="sell",
                asset_address=second_instrument["base_asset_address"],
                sub_id=int(second_instrument["base_asset_sub_id"]),
                price=Decimal("0"),  # will be set when quote is returned
                amount=Decimal("2"),
            ),
        ],
    )

    response = requests.post(
        "https://api-demo.lyra.finance/private/send_rfq",
        json={
            "subaccount_id": SUBACCOUNT_ID,
            **rfq_module_data.to_rfq_json(),
        },
        headers={
            **utils.sign_rest_auth_header(web3_client, SMART_CONTRACT_WALLET_ADDRESS, SESSION_KEY_PRIVATE_KEY),
            "accept": "application/json",
            "content-type": "application/json",
        },
    )

    ###############
    # Poll Quotes #
    ###############

    # can also use {wallet}.rfqs channel to listen for RFQs (same response format)
    time.sleep(3)
    response = requests.post(
        "https://api-demo.lyra.finance/private/poll_quotes",
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
        quote = response.json()["result"]["quotes"][0]
    except IndexError:
        print("No Quotes")
        return

    print("Received RFQ!", json.dumps(quote, indent=4))

    #######################
    # Sign execute action #
    #######################

    for index, leg in enumerate(rfq_module_data.legs):
        leg.price = Decimal(quote["legs"][index]["price"])

    action = SignedAction(
        subaccount_id=SUBACCOUNT_ID,
        owner=SMART_CONTRACT_WALLET_ADDRESS,
        signer=session_key_wallet.address,
        signature_expiry_sec=utils.MAX_INT_32,
        nonce=utils.get_action_nonce(),
        module_address=RFQ_MODULE_ADDRESS,
        module_data=rfq_module_data,
        DOMAIN_SEPARATOR=DOMAIN_SEPARATOR,
        ACTION_TYPEHASH=ACTION_TYPEHASH,
    )

    action.sign(session_key_wallet.key)

    #################
    # Execute Quote #
    #################

    response = requests.post(
        "https://api-demo.lyra.finance/private/execute_quote",
        json={
            **action.to_json(),
            "direction": rfq_module_data.quote_direction,  # NOTE: this direction MUST match the direction of the received quote
            "label": "",
            "rfq_id": quote["rfq_id"],  # using random rfq_id
            "quote_id": quote["quote_id"],  # using random qoute_id
        },
        headers={
            **utils.sign_rest_auth_header(web3_client, SMART_CONTRACT_WALLET_ADDRESS, SESSION_KEY_PRIVATE_KEY),
            "accept": "application/json",
            "content-type": "application/json",
        },
    )
    print("Quote Executed!")
    print(json.dumps(response.json(), indent=4))


if __name__ == "__main__":
    main()
