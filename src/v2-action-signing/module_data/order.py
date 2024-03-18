from web3 import Web3
from eth_abi.abi import encode


@dataclass
class TradeModuleData(SignedActionModuleData):
    asset: str
    sub_id: int
    limit_price: Decimal
    desired_amount: Decimal
    worst_fee: Decimal
    recipient_id: int
    is_bid: bool

    # metadata
    trade_id: str

    def to_abi_encoded(self):
        return encode(
            ["address", "uint", "int", "int", "uint", "uint", "bool"],
            [
                Web3.to_checksum_address(self.asset),
                self.sub_id,
                decimal_to_big_int(self.limit_price),
                decimal_to_big_int(self.desired_amount),
                decimal_to_big_int(self.worst_fee),
                self.recipient_id,
                self.is_bid,
            ],
        )
