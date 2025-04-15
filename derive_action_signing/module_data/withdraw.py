"""
Withdraw module data
"""
from dataclasses import dataclass
from .module_data import ModuleData
from decimal import Decimal
from web3 import Web3
from eth_abi.abi import encode


@dataclass
class WithdrawModuleData(ModuleData):
    asset: str
    amount: Decimal
    decimals: int
    asset_name: str

    def to_abi_encoded(self):

        amount_decimal = Decimal(self.amount)
        scaled_amount = int(amount_decimal.scaleb(self.decimals))
        return encode(
            ["address", "uint"],
            [
                Web3.to_checksum_address(self.asset),
                scaled_amount
            ],
        )
    def to_json(self):
        return {
            "amount": str(self.amount),
            "asset_name": self.asset_name,
            "is_atomic_signing": False,
        }