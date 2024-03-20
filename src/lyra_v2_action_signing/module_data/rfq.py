from dataclasses import dataclass
from decimal import Decimal
from typing import List
from web3 import Web3
from eth_abi.abi import encode
from hexbytes import HexBytes
from .module_data import ModuleData
from typing import Literal
from ..utils import decimal_to_big_int


@dataclass
class RFQQuoteDetails:
    instrument_name: str
    direction: Literal["buy", "sell"]
    asset_address: str
    sub_id: int
    price: Decimal
    amount: Decimal

    def to_eth_tx_params(self, quote_direction: Literal["buy", "sell"]):
        leg_sign = 1 if self.direction == "buy" else -1
        quote_sign = 1 if quote_direction == "buy" else -1
        return (
            Web3.to_checksum_address(self.asset_address),
            self.sub_id,
            decimal_to_big_int(self.price),
            decimal_to_big_int(self.amount) * leg_sign * quote_sign,
        )


@dataclass
class RFQQuoteModuleData(ModuleData):
    quote_direction: Literal["buy", "sell"]
    max_fee: Decimal
    trades: List[RFQQuoteDetails]

    """
    params:
    quote_direction: Literal["buy", "sell"] - The global direction of the whole quote. Note, RFQQuoteDetails.amount is always positive and 
                                              is passed into the API, but the global direction and leg direction determine the final encoded value.
    max_fee: Decimal - The maximum fee the user is willing to pay for the quote.
    trades: List[RFQQuoteDetails] - List of leg details for the quote.
    """

    def to_abi_encoded(self):
        return encode(
            ["(uint,(address,uint,uint,int)[])"],
            [
                (
                    decimal_to_big_int(self.max_fee),
                    [trade.to_eth_tx_params(self.quote_direction) for trade in self.trades],
                )
            ],
        )

    def to_json(self):
        legs = []
        for leg in self.trades:
            legs.append(
                {
                    "instrument_name": leg.instrument_name,
                    "direction": str(leg.direction),
                    "price": str(leg.price),
                    "amount": str(leg.amount),
                }
            )
        return {
            "legs": legs,
            "max_fee": str(self.max_fee),
        }


@dataclass
class RFQExecuteModuleData(RFQQuoteModuleData):
    """
    params:
    quote_direction: Literal["buy", "sell"] - Copy the quote_direction of the QUOTE which this execute is targeting.
                                              RFQQuoteDetails.amount is always positive and is passed into the API,
                                              but under the hood, amount sign is inverted and signed by executor.
    max_fee: Decimal - The maximum fee the user is willing to pay for the quote.
    trades: List[RFQQuoteDetails] - List of leg details for the quote which execute is targeting.
    """

    def _encoded_legs(self):
        encoded_legs = encode(
            ["(address,uint,uint,int)[]"],
            [
                # inverting direction of the signed quote
                [trade.to_eth_tx_params("buy" if self.quote_direction == "sell" else "sell") for trade in self.trades],
            ],
        )

        return encoded_legs

    def to_abi_encoded(self):
        return encode(
            ["bytes32", "uint"],
            [
                Web3.keccak(self._encoded_legs()),
                decimal_to_big_int(self.max_fee),
            ],
        )

    def to_json(self):
        legs = []
        for leg in self.trades:
            legs.append(
                {
                    "instrument_name": leg.instrument_name,
                    "direction": str(leg.direction),
                    "price": str(leg.price),
                    "amount": str(leg.amount),
                }
            )
        return {
            "legs": legs,
            "max_fee": str(self.max_fee),
        }
