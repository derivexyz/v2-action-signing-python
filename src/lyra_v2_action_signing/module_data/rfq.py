from dataclasses import dataclass
from decimal import Decimal
from typing import List
from web3 import Web3
from eth_abi.abi import encode
from hexbytes import HexBytes
from .module_data import ModuleData
from ..utils import decimal_to_big_int


@dataclass
class RFQQuoteDetails:
    asset: str
    sub_id: int
    price: Decimal
    amount: Decimal

    def to_eth_tx_params(self):
        return (
            Web3.to_checksum_address(self.asset),
            self.sub_id,
            decimal_to_big_int(self.price),
            decimal_to_big_int(self.amount),
        )


@dataclass
class RFQQuoteModuleData(ModuleData):
    max_fee: Decimal
    trades: List[RFQQuoteDetails]

    def to_abi_encoded(self):
        return encode(
            ["(uint,(address,uint,uint,int)[])"],
            [
                (
                    decimal_to_big_int(self.max_fee),
                    [trade.to_eth_tx_params() for trade in self.trades],
                )
            ],
        )


@dataclass
class RFQExecuteModuleData(ModuleData):
    order_hash: str
    max_fee: Decimal

    def to_abi_encoded(self):
        return encode(
            ["bytes32", "uint"],
            [
                HexBytes(self.order_hash),
                decimal_to_big_int(self.max_fee),
            ],
        )
