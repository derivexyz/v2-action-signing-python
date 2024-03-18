signed_order = SignedTradeOrder(
    subaccount_id=subaccount.subaccount_id,
    nonce=params["nonce"],
    module=TRADE_MODULE_ADDRESS,
    data=TradeModuleData(
        trade_id="",  # metadata not used in signature verification
        asset=instrument.base_asset.address,
        sub_id=int(instrument.base_asset.sub_id),
        limit_price=params["limit_price"],
        desired_amount=params["amount"],
        worst_fee=params["max_fee"],
        recipient_id=params["subaccount_id"],
        is_bid=params["direction"] == OrderDirection.BUY,
    ),
    expiry=params["signature_expiry_sec"],
    owner=subaccount.account.wallet,
    signer=params["signer"] if signer_wallet.address == params["signer"] else signer_wallet.address,
    signature="to-fill-in-next-step",
)

signature = signer_wallet.signHash(signed_order.to_typed_data_hash().hex())

# returns the HexBytes
return signature.signature.hex()