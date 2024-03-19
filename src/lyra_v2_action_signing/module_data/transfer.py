from dataclasses import dataclass
from .module_data import ModuleData
from decimal import Decimal
from web3 import Web3
from eth_abi.abi import encode
from typing import List
from ..utils import decimal_to_big_int


@dataclass
class TransferDetails:
    address: str
    sub_id: int
    amount: Decimal

    def to_eth_tx_params(self):
        return (
            Web3.to_checksum_address(self.address),
            self.sub_id,
            decimal_to_big_int(self.amount),
        )


@dataclass
class TransferModuleData(ModuleData):
    to_subaccount_id: int
    manager_for_new_account: str
    transfers: List[TransferDetails]

    # metadata
    # recipient data is empty bytes
    is_recipient_transfer: bool  # TODO: may need to remove this

    def to_abi_encoded(self):
        return (
            bytes.fromhex("")
            if self.is_recipient_transfer
            else encode(
                ["(uint,address,(address,uint,int)[])"],
                [
                    (
                        self.to_subaccount_id,
                        Web3.to_checksum_address(self.manager_for_new_account),
                        [t.to_eth_tx_params() for t in self.transfers],
                    )
                ],
            )
        )
