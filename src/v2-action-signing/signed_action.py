@dataclass
class SignedAction(JSONDataClass):
    subaccount_id: int
    nonce: int
    module: str
    expiry: int
    owner: str
    signer: str
    signature: str
    data: SignedActionModuleData

    def validate_signature(self):
        data_hash = self.to_typed_data_hash()
        recovered = Account._recover_hash(
            data_hash.hex(),
            signature=HexBytes(self.signature),
        )

        if recovered.lower() != self.signer.lower():
            raise Error("Invalid signature")

    def to_typed_data_hash(self):
        return Web3.keccak(bytes.fromhex("1901") + DOMAIN_SEPARATOR + self.get_action_hash())

    def get_action_hash(self):
        return Web3.keccak(
            encode(
                [
                    "bytes32",
                    "uint",
                    "uint",
                    "address",
                    "bytes32",
                    "uint",
                    "address",
                    "address",
                ],
                [
                    ACTION_TYPEHASH,
                    self.subaccount_id,
                    self.nonce,
                    Web3.to_checksum_address(self.module),
                    Web3.keccak(self.data.to_abi_encoded()),
                    self.expiry,
                    Web3.to_checksum_address(self.owner),
                    Web3.to_checksum_address(self.signer),
                ],
            )
        )

    def to_eth_tx_params(self):
        return (
            self.subaccount_id,
            self.nonce,
            Web3.to_checksum_address(self.module),
            self.data.to_abi_encoded(),
            self.expiry,
            Web3.to_checksum_address(self.owner),
            Web3.to_checksum_address(self.signer),
            # bytes.fromhex(self.signature[2:]),
        )

    def sign(self):
        signature = signer_wallet.signHash(signed_order.to_typed_data_hash().hex())

        # returns the HexBytes
        return signature.signature.hex()
