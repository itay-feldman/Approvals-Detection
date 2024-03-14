import click

from typing import List
from web3 import Web3
from web3.types import LogReceipt
from pyproval.consts import APPROVAL_EVENT_TOPIC, INFURA_API_URL


def get_topic_from_address(address: str) -> str:
    # This is an ugly but simple way to do this conversion
    topic = "0x" + "0" * 24 + address[2:]
    return topic.lower()


def get_approval_events(address: str) -> List[LogReceipt]:
    # Create w3 object
    w3 = Web3(Web3.HTTPProvider(INFURA_API_URL))
    # Filter by topics, topic 0 is the event type, topic 1 is the owner
    filter_args = {
        "fromBlock": 0,
        "toBlock": "latest",
        "topics": [
            APPROVAL_EVENT_TOPIC,
            get_topic_from_address(address)
        ]
    }
    w3_filter = w3.eth.filter(filter_args)  # type: ignore
    # Take all of these logs in order, the thirds topic (index 2) is the
    #   recipient and the uint256 data is the amount of allowance
    return w3_filter.get_all_entries()


@click.group('PyProval')
@click.option("--address", required=True, help="Address of account to check approval history on")
def check_approvals():
    # Call approval checker here
    # Using the approval logs list, print everything here
    pass
