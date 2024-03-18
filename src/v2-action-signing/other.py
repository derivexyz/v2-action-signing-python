def _sign_order(self, order, base_asset_sub_id, instrument_type, currency):
    trade_module_data = self._encode_trade_data(order, base_asset_sub_id, instrument_type, currency)
    encoded_action_hash = eth_abi.encode(
        ["bytes32", "uint256", "uint256", "address", "bytes32", "uint256", "address", "address"],
        [
            bytes.fromhex(self.contracts["ACTION_TYPEHASH"][2:]),
            order["subaccount_id"],
            order["nonce"],
            self.contracts["TRADE_MODULE_ADDRESS"],
            trade_module_data,
            order["signature_expiry_sec"],
            self.wallet,
            order["signer"],
        ],
    )

    action_hash = self.web3_client.keccak(encoded_action_hash)
    encoded_typed_data_hash = "".join(["0x1901", self.contracts["DOMAIN_SEPARATOR"][2:], action_hash.hex()[2:]])
    typed_data_hash = self.web3_client.keccak(hexstr=encoded_typed_data_hash)
    order["signature"] = self.signer.signHash(typed_data_hash).signature.hex()
    return order
