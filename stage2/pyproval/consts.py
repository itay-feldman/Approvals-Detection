import json
from pyproval.erc20_abi import _ERC20_ABI

# This is calculated by taking the keccak-256 hash of "cleaned" signature of the event
# So no names or keywords just: "Approval(address,address,uint256)"
APPROVAL_EVENT_TOPIC = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"

# You can very much change this
INFURA_API_TOKEN = "1c25ea3e0dc04dd6b9d2b7f90188b6d2"
INFURA_API_URL = f"https://mainnet.infura.io/v3/{INFURA_API_TOKEN}"
APPROVAL_EVENT_SENDER_ADDRESS_TOPIC_INDEX = 1
APPROVAL_EVENT_RECIPIENT_ADDRESS_TOPIC_INDEX = 2
ETHEREUM_ADDRESS_HEX_LENGTH = 40

ERC20_CONTRACT_ABI = json.dumps(_ERC20_ABI)
