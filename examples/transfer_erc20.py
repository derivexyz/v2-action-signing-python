####################################################################
# We highly recommend transfering erc20 via UX instead of manually #
####################################################################

# https://docs.lyra.finance/docs/transfer

# NOTE:
# There are 3 types of transfers, each using different module data types:
# 1. private/transfer_erc20 routes uses the TransferERC20ModuleData type for signatures
# 2. private/transfer_position route uses the TradeModuleData type for signatures
# 3. private/transfer_positions (plural) uses the MakerTransferPositionsModuleData and TakerTransferPositionsModuleData types for signatures

# This example goes over #1

import requests
import json
from web3 import Web3
from decimal import Decimal

from lyra_v2_action_signing import (
    SignedAction,
    TransferERC20Details,
    SenderTransferERC20ModuleData,
    RecipientTransferERC20ModuleData,
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

    # NOTE: make sure recipient has enough margin to accept this transfer
    FROM_SUBACCOUNT_ID = 30769
    TO_SUBACCOUNT_ID = 31049

    #############################################
    # Protocol Constants from docs.lyra.finance #
    #############################################

    DOMAIN_SEPARATOR = "0x9bcf4dc06df5d8bf23af818d5716491b995020f377d3b7b64c29ed14e3dd1105"
    ACTION_TYPEHASH = "0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17"
    TRANSFER_ERC20_MODULE_ADDRESS = "0x0CFC1a4a90741aB242cAfaCD798b409E12e68926"
    CASH_ASSET_ADDRESS = "0x6caf294DaC985ff653d5aE75b4FF8E0A66025928"  # NOT the ERC20.sol address
    # For Non-CASH collateral transfers use the BaseAsset.sol address under each market table in "Protocol Constants"

    ###################
    # Define Transfer #
    ###################

    transfer_details = TransferERC20Details(
        base_address=CASH_ASSET_ADDRESS,
        sub_id=0,  # always 0 for base assets
        amount=Decimal("123"),
    )

    sender_action = SignedAction(
        subaccount_id=FROM_SUBACCOUNT_ID,
        owner=SMART_CONTRACT_WALLET_ADDRESS,
        signer=session_key_wallet.address,
        signature_expiry_sec=utils.MAX_INT_32,
        nonce=utils.get_action_nonce(),
        module_address=TRANSFER_ERC20_MODULE_ADDRESS,
        module_data=SenderTransferERC20ModuleData(
            to_subaccount_id=TO_SUBACCOUNT_ID,
            transfers=[transfer_details],
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
        module_address=TRANSFER_ERC20_MODULE_ADDRESS,
        module_data=RecipientTransferERC20ModuleData(),
        DOMAIN_SEPARATOR=DOMAIN_SEPARATOR,
        ACTION_TYPEHASH=ACTION_TYPEHASH,
    )

    recipient_action.sign(session_key_wallet.key)

    #####################
    # Initiate Transfer #
    #####################

    print("TO JSON", sender_action.to_json())
    response = requests.post(
        "https://api-demo.lyra.finance/private/transfer_erc20",
        json={
            "subaccount_id": sender_action.subaccount_id,
            "recipient_subaccount_id": recipient_action.subaccount_id,
            "sender_details": {
                "nonce": sender_action.nonce,
                "signature": sender_action.signature,
                "signature_expiry_sec": sender_action.signature_expiry_sec,
                "signer": sender_action.signer,
            },
            "recipient_details": {
                "nonce": recipient_action.nonce,
                "signature": recipient_action.signature,
                "signature_expiry_sec": recipient_action.signature_expiry_sec,
                "signer": recipient_action.signer,
            },
            "transfer": {
                "address": CASH_ASSET_ADDRESS,
                "amount": str(transfer_details.amount),
                "sub_id": str(transfer_details.sub_id),
            },
        },
        headers={
            **utils.sign_rest_auth_header(web3_client, SMART_CONTRACT_WALLET_ADDRESS, SESSION_KEY_PRIVATE_KEY),
            "accept": "application/json",
            "content-type": "application/json",
        },
    )
    print("Got Transfer ERC20 Response", json.dumps(response.json(), indent=4))


if __name__ == "__main__":
    main()
