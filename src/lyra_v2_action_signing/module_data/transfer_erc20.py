from dataclasses import dataclass
from .module_data import ModuleData
from decimal import Decimal
from web3 import Web3
from eth_abi.abi import encode
from typing import List
from ..utils import decimal_to_big_int


@dataclass
class TransferERC20Details:
    base_address: str
    sub_id: int
    amount: Decimal

    def to_eth_tx_params(self):
        return (
            Web3.to_checksum_address(self.base_address),
            self.sub_id,
            decimal_to_big_int(self.amount),
        )


@dataclass
class SenderTransferERC20ModuleData(ModuleData):
    to_subaccount_id: int
    transfers: List[TransferERC20Details]
    manager_if_new_account: str = "0x0000000000000000000000000000000000000000"

    def to_abi_encoded(self):
        return encode(
            ["(uint,address,(address,uint,int)[])"],
            [
                (
                    self.to_subaccount_id,
                    Web3.to_checksum_address(self.manager_if_new_account),
                    [t.to_eth_tx_params() for t in self.transfers],
                )
            ],
        )

    def to_json(self):
        return {}


@dataclass
class RecipientTransferERC20ModuleData(ModuleData):
    def to_abi_encoded(self):
        return bytes.fromhex("")

    def to_json(self):
        return {}
