from dataclasses import dataclass, field
from typing import Literal, List
from decimal import Decimal
from .module_data import ModuleData
from .rfq import RFQQuoteDetails, RFQQuoteModuleData, RFQExecuteModuleData


@dataclass
class TransferPositionsDetails(RFQQuoteDetails):
    pass


@dataclass
class MakerTransferPositionsModuleData(ModuleData):
    global_direction: Literal["buy", "sell"]
    positions: List[TransferPositionsDetails]

    _internal_quote_module_data: RFQQuoteModuleData = field(init=False, default=None)

    def __post_init__(self):
        self._internal_quote_module_data = RFQQuoteModuleData(
            global_direction=self.global_direction,
            max_fee=Decimal("0"),
            legs=self.positions,
        )

    def to_abi_encoded(self):
        return self._internal_quote_module_data.to_abi_encoded()

    def to_json(self):
        return self._internal_quote_module_data.to_json()


@dataclass
class TakerTransferPositionsModuleData(ModuleData):
    global_direction: Literal["buy", "sell"]
    positions: List[TransferPositionsDetails]

    _internal_execute_module_data: RFQExecuteModuleData = field(init=False, default=None)

    def __post_init__(self):
        self._internal_execute_module_data = RFQExecuteModuleData(
            global_direction=self.global_direction,
            max_fee=Decimal("0"),
            legs=self.positions,
        )

    def to_abi_encoded(self):
        return self._internal_execute_module_data.to_abi_encoded()

    def to_json(self):
        return self._internal_execute_module_data.to_json()
