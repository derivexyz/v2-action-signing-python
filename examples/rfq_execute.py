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

    url = "https://api-demo.lyra.finance/public/get_instrument"
    response = requests.post(
        url,
        json={
            "instrument_name": "ETH-20240329-3200-C",
        },
        headers={"accept": "application/json", "content-type": "application/json"},
    )
    first_instrument = response.json()["result"]

    response = requests.post(
        url,
        json={
            "instrument_name": "ETH-20240329-3200-P",
        },
        headers={"accept": "application/json", "content-type": "application/json"},
    )
    second_instrument = response.json()["result"]

    #############
    # Send RFQs #
    #############

    # Below action results in a "short" first_instrument position and "long" second_instrument position
    rfq_module_data = RFQExecuteModuleData(
        global_direction="buy",
        max_fee=Decimal("1000"),
        legs=[
            RFQQuoteDetails(
                instrument_name=first_instrument["instrument_name"],
                direction="sell",
                asset_address=first_instrument["base_asset_address"],
                sub_id=int(first_instrument["base_asset_sub_id"]),
                price=Decimal("0"),  # will be set when quote is returned
                amount=Decimal("1"),
            ),
            RFQQuoteDetails(
                instrument_name=second_instrument["instrument_name"],
                direction="buy",
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
    print("Got RFQ Response", json.dumps(response.json(), indent=4))

    ###############
    # Poll Quotes #
    ###############

    # can also use {wallet}.rfqs channel to listen for RFQs (same response format)
    time.sleep(5)
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

    print("Received Quotes!", json.dumps(response.json()["result"]["quotes"], indent=4))

    quote = None
    for current_quote in response.json()["result"]["quotes"]:
        # The received quote direction must be the opposite of the RFQ direction
        if current_quote["direction"] != rfq_module_data.global_direction:
            quote = current_quote
            break

    if quote is None:
        print(f"No Quotes for {first_instrument['instrument_name']} and {second_instrument['instrument_name']}")
        return

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
            "label": "",
            "rfq_id": quote["rfq_id"],
            "quote_id": quote["quote_id"],
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
