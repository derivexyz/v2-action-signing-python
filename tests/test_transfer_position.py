# Manual Python example is WIP. Please use the multiple position transfer endpoint `private/transfer_positions` in the meantime.

# NOTE:
# There are 3 types of transfers, each using different module data types:
# 1. private/transfer_erc20 routes uses the TransferERC20ModuleData type for signatures
# 2. private/transfer_position route uses the TradeModuleData type for signatures
# 3. private/transfer_positions (plural) uses the MakerTransferPositionsModuleData and TakerTransferPositionsModuleData types for signatures
# NOTE:
# There are 3 types of transfers, each using different module data types:
# 1. private/transfer_erc20 routes uses the TransferERC20ModuleData type for signatures
# 2. private/transfer_position route uses the TradeModuleData type for signatures
# 3. private/transfer_positions (plural) uses the MakerTransferPositionsModuleData and TakerTransferPositionsModuleData types for signatures

# This example goes over #2

import requests
from web3 import Web3
from decimal import Decimal
from derive_action_signing import (
    SignedAction,
    TradeModuleData,
)
from derive_action_signing.utils import (
    MAX_INT_32,
    get_action_nonce,
    sign_rest_auth_header,
)


from rich import print


def test_transfer_positions(
    domain_separator,
    action_typehash,
    module_addresses,
):
    ########################################
    # Get existing testnet subaccount info #
    ########################################
    # SMART_CONTRACT_WALLET_ADDRESS
    DERIVE_CONTRACT_WALLET_ADDRESS = "0xeda0656dab4094C7Dc12F8F12AF75B5B3Af4e776"
    SESSION_KEY_PRIVATE_KEY = (
        "0x83ee63dc6655509aabce0f7e501a31c511195e61e9d0e9917f0a55fd06041a66"
    )
    web3_client = Web3()
    session_key_wallet = web3_client.eth.account.from_key(SESSION_KEY_PRIVATE_KEY)

    FROM_SUBACCOUNT_ID = 137402
    TO_SUBACCOUNT_ID = 137404

    # Get a currently active instrument
    url = "https://api-demo.lyra.finance/public/get_instruments"
    response = requests.post(
        url,
        json={"currency": "ETH", "instrument_type": "option", "expired": False},
        headers={"accept": "application/json", "content-type": "application/json"},
    )
    instruments = response.json()["result"]
    # Find an active instrument
    active_instruments = [inst for inst in instruments if inst["is_active"]]
    if not active_instruments:
        print("No active instruments found")
        return
    instrument = active_instruments[0]  # Use the first active instrument
    print(f"Selected instrument for transfer: {instrument['instrument_name']}")

    ###################
    # Define Transfer #
    ###################

    # Transfer amount and price for the position (matching opened position)
    transfer_amount = Decimal("1")
    transfer_price = Decimal("100")
    max_fee = Decimal("1000")

    # For transfer_position, we need to create orders that include all required fields
    # in the signature. Let's try using the basic order structure that includes
    # direction and instrument_name as part of the signed data.

    # For now, let's create basic signed actions and see if we can modify the signing
    maker_action = SignedAction(
        subaccount_id=FROM_SUBACCOUNT_ID,
        owner=DERIVE_CONTRACT_WALLET_ADDRESS,
        signer=session_key_wallet.address,
        signature_expiry_sec=MAX_INT_32,
        nonce=get_action_nonce(),
        module_address=module_addresses["trade"],
        module_data=TradeModuleData(
            asset_address=instrument["base_asset_address"],
            sub_id=int(instrument["base_asset_sub_id"]),
            limit_price=transfer_price,
            amount=transfer_amount,
            max_fee=max_fee,
            recipient_id=FROM_SUBACCOUNT_ID,
            is_bid=True,
        ),
        DOMAIN_SEPARATOR=domain_separator,
        ACTION_TYPEHASH=action_typehash,
    )

    taker_action = SignedAction(
        subaccount_id=TO_SUBACCOUNT_ID,
        owner=DERIVE_CONTRACT_WALLET_ADDRESS,
        signer=session_key_wallet.address,
        signature_expiry_sec=MAX_INT_32,
        nonce=get_action_nonce(),
        module_address=module_addresses["trade"],
        module_data=TradeModuleData(
            asset_address=instrument["base_asset_address"],
            sub_id=int(instrument["base_asset_sub_id"]),
            limit_price=transfer_price,
            amount=transfer_amount,
            max_fee=max_fee,
            recipient_id=TO_SUBACCOUNT_ID,
            is_bid=False,
        ),
        DOMAIN_SEPARATOR=domain_separator,
        ACTION_TYPEHASH=action_typehash,
    )

    # Sign the actions
    maker_action.sign(session_key_wallet.key)
    taker_action.sign(session_key_wallet.key)
    #####################
    # Initiate Transfer #
    #####################

    # Create transfer_position specific parameters
    # All these fields must be included in the signature for transfer_position
    maker_params = {
        "direction": "buy",
        "instrument_name": instrument["instrument_name"],
        **maker_action.to_json(),
    }

    taker_params = {
        "direction": "sell",
        "instrument_name": instrument["instrument_name"],
        **taker_action.to_json(),
    }

    print(f"Using instrument: {instrument['instrument_name']}")
    print(f"Transfer amount: {transfer_amount}")
    # print("DEBUG: Maker params:", json.dumps(maker_params, indent=2, default=str))
    # print("DEBUG: Taker params:", json.dumps(taker_params, indent=2, default=str))

    response = requests.post(
        "https://api-demo.lyra.finance/private/transfer_position_debug",
        json={
            "wallet": DERIVE_CONTRACT_WALLET_ADDRESS,
            "maker_params": maker_params,
            "taker_params": taker_params,
        },
        headers={
            **sign_rest_auth_header(
                web3_client, DERIVE_CONTRACT_WALLET_ADDRESS, SESSION_KEY_PRIVATE_KEY
            ),
            "accept": "application/json",
            "content-type": "application/json",
        },
    )

    response_data = response.json().get("result")

    # verify the maker and taker results
    ## verify encoded abi data
    assert (
        "0x" + maker_action.module_data.to_abi_encoded().hex()
        == response_data["maker_result"]["encoded_data"]
    )
    assert (
        "0x" + taker_action.module_data.to_abi_encoded().hex()
        == response_data["taker_result"]["encoded_data"]
    )

    ## Verify action hash
    assert (
        "0x" + maker_action._get_action_hash().hex()
        == response_data["maker_result"]["action_hash"]
    ), (
        f"expected: {maker_action._get_action_hash()}, ",
        f"actual: {response_data['maker_result']['action_hash']}",
    )
    assert (
        "0x" + taker_action._get_action_hash().hex()
        == response_data["taker_result"]["action_hash"]
    ), (
        f"expected: {taker_action._get_action_hash()}, ",
        f"actual: {response_data['taker_result']['action_hash']}",
    )
    ## Verify typed data hash
    assert (
        "0x" + maker_action._to_typed_data_hash().hex()
        == response_data["maker_result"]["typed_data_hash"]
    ), (
        f"expected: {maker_action._to_typed_data_hash()}, "
        + f"actual: {response_data['maker_result']['typed_data_hash']}"
    )
    assert (
        "0x" + taker_action._to_typed_data_hash().hex()
        == response_data["taker_result"]["typed_data_hash"]
    ), (
        f"expected: {taker_action._to_typed_data_hash()}, "
        + f"actual: {response_data['taker_result']['typed_data_hash']}"
    )
