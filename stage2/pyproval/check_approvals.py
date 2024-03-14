import click

from collections import OrderedDict
from typing import List
from web3 import Web3
from web3.types import LogReceipt
from pyproval import consts


def get_topic_from_address(address: str) -> str:
    # This is an ugly but simple way to do this conversion
    topic = "0x" + "0" * 24 + address[2:]
    return topic.lower()


def get_approval_events(address: str) -> List[LogReceipt]:
    # Create w3 object
    w3 = Web3(Web3.HTTPProvider(consts.INFURA_API_URL))
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
        recipient_address = approval["topics"][consts.APPROVAL_EVENT_RECIPIENT_ADDRESS_TOPIC_INDEX].hex()
        # Since the list is ordered, we know that a value with the same recipient should always override
        # the previous value with the same recipient.
        latest_approvals[recipient_address] = approval
    return list(latest_approvals.values())


@click.group('PyProval')
@click.option("--address", type=str, required=True, help="Address of account to check approval history on")
def check_approvals(address: str):
    # Call approval checker here
    all_approvals = get_approval_events(address)
    # Filter out redundant approvals
    latest_approvals = filter_for_latest_approvals(all_approvals)
    # Using the approval logs list, print everything here
    for approval in latest_approvals:
        pass
