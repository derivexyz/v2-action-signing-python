import pytest
from v2_action_signing import SignedAction, TradeModuleData

# Uses Testnet for all testing


def test_sign_order():

    ###############################################################################
    # Constants taken from https://docs.lyra.finance/reference/protocol-constants #
    ###############################################################################

    ############################################
    # Get sub_id and asset address from ticker #
    ############################################

    action = SignedAction(
        subaccount_id=0,
        owner="0x...",
        signature_expiry_sec="0x...",
        nonce="0x...",
        module_address="0x...",
        module_data=TradeModuleData(
            asset="0x...",
            sub_id=0,
            limit_price=0.0,
            desired_amount=0.0,
            worst_fee=0.0,
            recipient_id=0,
            is_bid=True,
        ),
        DOMAIN_SEPARATOR="0x...",
        ACTION_TYPEHASH="0x...",
    )

    action.sign("0x...")

    assert action.signature is not None
