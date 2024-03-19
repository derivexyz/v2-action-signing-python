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

    def to_abi_encoded(self):
        return encode(
            ["address", "uint"],
            [
                Web3.to_checksum_address(self.asset),
                int(self.amount * Decimal(10) ** self.decimals),
            ],
        )
