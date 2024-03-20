from decimal import Decimal
import random
from datetime import datetime, timezone
from web3 import Web3
from eth_account.messages import encode_defunct

MAX_INT_256 = 2**255 - 1
MIN_INT_256 = -(2**255)
MAX_INT_32 = 2**31 - 1


def decimal_to_big_int(value: Decimal) -> int:
    result_value = int(value * Decimal(10**18))
    if result_value < MIN_INT_256 or result_value > MAX_INT_256:
        raise ValueError(f"resulting integer value must be between {MIN_INT_256} and {MAX_INT_256}")
    return result_value


def get_action_nonce(nonce_iter: int = 0) -> int:
    """
    Used to generate a unique nonce to prevent replay attacks on-chain.

    Uses the current UTC timestamp in milliseconds and a random number up to 3 digits.

    :param nonce_iter: allows to enter a specific number between 0 and 999 unless. If None is passed a random number is chosen
    """
    if nonce_iter is None:
        nonce_iter = random.randint(0, 999)
    return int(str(utc_now_ms()) + str(nonce_iter))


def utc_now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def sign_rest_auth_header(web3_client: Web3, smart_contract_wallet: str, session_key_or_wallet_private_key: str):
    timestamp = str(utc_now_ms())
    signature = web3_client.eth.account.sign_message(
        encode_defunct(text=timestamp), private_key=session_key_or_wallet_private_key
    ).signature.hex()
    return {
        "X-LYRAWALLET": smart_contract_wallet,
        "X-LYRATIMESTAMP": str(timestamp),
        "X-LYRASIGNATURE": signature,
    }


def sign_ws_login(web3_client: Web3, smart_contract_wallet: str, session_key_or_wallet_private_key: str):
    timestamp = str(utc_now_ms())
    signature = web3_client.eth.account.sign_message(
        encode_defunct(text=timestamp), private_key=session_key_or_wallet_private_key
    ).signature.hex()
    return {
        "wallet": smart_contract_wallet,
        "timestamp": str(timestamp),
        "signature": signature,
    }
