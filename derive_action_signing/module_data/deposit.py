"""
Deposit module data.
"""
from dataclasses import dataclass
from .module_data import ModuleData
from decimal import Decimal
from web3 import Web3
from eth_abi.abi import encode


@dataclass
class DepositModuleData(ModuleData):
    amount: Decimal
    asset: str
    manager: str

    # metadata
    decimals: int

    def to_abi_encoded(self):
        amount_decimal = Decimal(self.amount)
        scaled_amount = int(amount_decimal.scaleb(self.decimals))
        return encode(
            ["uint256", "address", "address"],
            [
                scaled_amount,
                Web3.to_checksum_address(self.asset),
                Web3.to_checksum_address(self.manager),
            ],
        )

    def to_json(self):
        return {
            "amount": str(self.amount),
            "asset_name": "USDC",
            "is_atomic_signing": False,
        }