from collections import OrderedDict
from eth_typing import ChecksumAddress
from typing import List, Optional
from web3 import Web3
from web3.types import LogReceipt
from pyproval import consts


def is_valid_address(address: str) -> bool:
    return Web3.is_address(address)


def get_web3():
    return Web3(Web3.HTTPProvider(consts.INFURA_API_URL))


def get_topic_from_address(address: str) -> str:
    # This is an ugly but simple way to do this conversion
    topic = "0x" + "0" * 24 + address[2:]
    return topic.lower()


def get_approval_events(address: str) -> List[LogReceipt]:
    # Create w3 object
    w3 = get_web3()
    # Filter by topics, topic 0 is the event type, topic 1 is the owner
    filter_args = {
        "fromBlock": 0,
        "toBlock": "latest",
        "topics": [
            consts.APPROVAL_EVENT_TOPIC,
            get_topic_from_address(address)
        ]
    }
    w3_filter = w3.eth.filter(filter_args)  # type: ignore
    # Take all of these logs in order, the thirds topic (index 2) is the
    #   recipient and the uint256 data is the amount of allowance
    return w3_filter.get_all_entries()


def get_spender_hex_address(approval: LogReceipt) -> str:
    return approval["topics"][consts.APPROVAL_EVENT_RECIPIENT_ADDRESS_TOPIC_INDEX].hex()


def filter_for_latest_approvals(approvals: List[LogReceipt]) -> List[LogReceipt]:
    """New approvals override older ones so it is useful to filter out redundant approval events.
    The list of log receipts is expected to contain all approvals of the same account, like the
    list returned by get_approval_events, so the second topic (the owner) isn't checked, it is also
    expected that the list is ordered.
    Since some values are removed and others are preserved, the order of the resulting list is not
    guaranteed to reflect an actual timeline (i.e. the approvals are not necessarily chronological),
    re-ordering the list can be achieved by using the block and transaction indexes in each log.
    """
    latest_approvals: OrderedDict[str, LogReceipt] = OrderedDict()
    for approval in approvals:
        # We use the hex representation of the "recipient topic" as the key
        recipient_address = get_spender_hex_address(approval)
        # Since the list is ordered, we know that a value with the same recipient should always override
        # the previous value with the same recipient.
        latest_approvals[recipient_address] = approval
    return list(latest_approvals.values())


def get_contract(contract_address: ChecksumAddress):
    w3 = get_web3()
    return w3.eth.contract(contract_address, abi=consts.ERC20_CONTRACT_ABI)


def get_amount_from_approval(approval: LogReceipt) -> Optional[int]:
    data = approval["data"].hex().lower().strip("0x")
    if data:
        return int(data, 16)
    return None
