# NOTE:
# There are 3 types of transfers, each using different module data types:
# 1. private/transfer_erc20 routes uses the TransferERC20ModuleData type for signatures
# 2. private/transfer_position route uses the TradeModuleData type for signatures
# 3. private/transfer_positions (plural) uses the MakerTransferPositionsModuleData and TakerTransferPositionsModuleData types for signatures

# The below example is for #3

import json
import requests
from web3 import Web3
from decimal import Decimal
from lyra_v2_action_signing import (
    SignedAction,
    TransferPositionsDetails,
    MakerTransferPositionsModuleData,
    TakerTransferPositionsModuleData,
    utils,
)


def main():
    # NOTE: before quoting RFQ, reach out to Lyra Exchange to be approved for RFQ quoting

    ########################################
    # Get existing testnet subaccount info #
    ########################################

    SMART_CONTRACT_WALLET_ADDRESS = "0x8772185a1516f0d61fC1c2524926BfC69F95d698"
    SESSION_KEY_PRIVATE_KEY = "0x2ae8be44db8a590d20bffbe3b6872df9b569147d3bf6801a35a28281a4816bbd"
    web3_client = Web3()
    session_key_wallet = web3_client.eth.account.from_key(SESSION_KEY_PRIVATE_KEY)

    FROM_SUBACCOUNT_ID = 30769
    TO_SUBACCOUNT_ID = 31049

    #############################################
    # Protocol Constants from docs.lyra.finance #
    #############################################

    DOMAIN_SEPARATOR = "0x9bcf4dc06df5d8bf23af818d5716491b995020f377d3b7b64c29ed14e3dd1105"
    ACTION_TYPEHASH = "0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17"
    # multi-position transfers use RFQ_MODULE_ADDRESS
    RFQ_MODULE_ADDRESS = "0x4E4DD8Be1e461913D9A5DBC4B830e67a8694ebCa"

    ###################################
    # Get two random live instruments #
    ###################################

    url = "https://api-demo.lyra.finance/public/get_instrument"
    response = requests.post(
        url,
        json={
            "instrument_name": "ETH-20240329-1600-C",
        },
        headers={"accept": "application/json", "content-type": "application/json"},
    )
    first_instrument = response.json()["result"]

    response = requests.post(
        url,
        json={
            "instrument_name": "ETH-20240329-1600-P",
        },
        headers={"accept": "application/json", "content-type": "application/json"},
    )
    second_instrument = response.json()["result"]

    ###################
    # Define Transfer #
    ###################

    # Below action results in a "short" first_instrument position and "long" second_instrument position
    positions = [
        TransferPositionsDetails(
            instrument_name=first_instrument["instrument_name"],
            direction="sell",
            asset_address=first_instrument["base_asset_address"],
            sub_id=int(first_instrument["base_asset_sub_id"]),
            price=Decimal("75"),
            amount=Decimal("0.1"),
        ),
        TransferPositionsDetails(
            instrument_name=second_instrument["instrument_name"],
            direction="buy",
            asset_address=second_instrument["base_asset_address"],
            sub_id=int(second_instrument["base_asset_sub_id"]),
            price=Decimal("50"),
            amount=Decimal("0.2"),
        ),
    ]

    sender_action = SignedAction(
        subaccount_id=FROM_SUBACCOUNT_ID,
        owner=SMART_CONTRACT_WALLET_ADDRESS,
        signer=session_key_wallet.address,
        signature_expiry_sec=utils.MAX_INT_32,
        nonce=utils.get_action_nonce(),
        module_address=RFQ_MODULE_ADDRESS,
        module_data=MakerTransferPositionsModuleData(
            global_direction="buy",
            positions=positions,
        ),
        DOMAIN_SEPARATOR=DOMAIN_SEPARATOR,
        ACTION_TYPEHASH=ACTION_TYPEHASH,
    )

    sender_action.sign(session_key_wallet.key)

    recipient_action = SignedAction(
        subaccount_id=TO_SUBACCOUNT_ID,
        owner=SMART_CONTRACT_WALLET_ADDRESS,
        signer=session_key_wallet.address,
        signature_expiry_sec=utils.MAX_INT_32,
        nonce=utils.get_action_nonce(),
        module_address=RFQ_MODULE_ADDRESS,
        module_data=TakerTransferPositionsModuleData(
            global_direction="sell",  # recipient direction must be the opposite to senders
            positions=positions,
        ),
        DOMAIN_SEPARATOR=DOMAIN_SEPARATOR,
        ACTION_TYPEHASH=ACTION_TYPEHASH,
    )

    recipient_action.sign(session_key_wallet.key)

    #####################
    # Initiate Transfer #
    #####################

    response = requests.post(
        "https://api-demo.lyra.finance/private/transfer_positions",
        json={
            "wallet": SMART_CONTRACT_WALLET_ADDRESS,
            "maker_params": sender_action.to_json(),
            "taker_params": recipient_action.to_json(),
        },
        headers={
            **utils.sign_rest_auth_header(web3_client, SMART_CONTRACT_WALLET_ADDRESS, SESSION_KEY_PRIVATE_KEY),
            "accept": "application/json",
            "content-type": "application/json",
        },
    )
    print("Got RFQ Response", json.dumps(response.json(), indent=4))


if __name__ == "__main__":
    main()
