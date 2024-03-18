import pytest
from v2_action_signing import SignedAction, TradeModuleData

# Uses Testnet for all testing

###############################################################################
# Constants taken from https://docs.lyra.finance/reference/protocol-constants #
###############################################################################


def test_sign_order(domain_separator, action_typehash, module_addresses, random_live_instrument_ticker):

    ############################################
    # Get sub_id and asset address from ticker #
    ############################################

    subaccount_id = 1
    action = SignedAction(
        subaccount_id=subaccount_id,
        owner="0x...",
        signature_expiry_sec="0x...",
        nonce="0x...",
        module_address=module_addresses["trade"],
        module_data=TradeModuleData(
            asset=random_live_instrument_ticker["base_asset_address"],
            sub_id=int(random_live_instrument_ticker["base_asset_sub_id"]),
            limit_price=0.0,
            desired_amount=0.0,
            worst_fee=0.0,
            recipient_id=subaccount_id,
            is_bid=True,
        ),
        DOMAIN_SEPARATOR=domain_separator,
        ACTION_TYPEHASH=action_typehash,
    )

    action.sign("0x...")

    assert action.signature is not None
