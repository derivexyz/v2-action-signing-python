from decimal import Decimal
from web3 import Web3
from eth_abi.abi import encode
from dataclasses import dataclass
from .module_data import ModuleData
from ..utils import decimal_to_big_int


@dataclass
class TradeModuleData(ModuleData):
    asset_address: str
    sub_id: int
    limit_price: Decimal
    amount: Decimal
    max_fee: Decimal
    recipient_id: int
    is_bid: bool

    def to_abi_encoded(self):
        return encode(
            ["address", "uint", "int", "int", "uint", "uint", "bool"],
            [
                Web3.to_checksum_address(self.asset_address),
                self.sub_id,
                decimal_to_big_int(self.limit_price),
                decimal_to_big_int(self.amount),
                decimal_to_big_int(self.max_fee),
                self.recipient_id,
                self.is_bid,
            ],
        )

    def to_json(self):
        return {
            "limit_price": str(self.limit_price),
            "amount": str(self.amount),
            "max_fee": str(self.max_fee),
        }
