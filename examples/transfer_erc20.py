###############################################################################
# We highly recommend transfering erc20 via UX instead of manually #
###############################################################################

# https://docs.lyra.finance/docs/transfer

# Manual Python example is WIP.

# NOTE:
# There are 3 types of transfers, each using different module data types:
# 1. private/transfer_erc20 routes uses the TransferERC20ModuleData type for signatures
# 2. private/transfer_position route uses the TradeModuleData type for signatures
# 3. private/transfer_positions (plural) uses the RFQQuoteModuleData and RFQExecuteModuleData types for signatures
