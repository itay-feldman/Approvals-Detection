from collections import OrderedDict
from eth_typing import ChecksumAddress
from pydantic import BaseModel
from typing import List, Optional
from web3 import Web3
from web3.types import LogReceipt
from pyproval import consts


class Erc20ApprovalData(BaseModel):
    contract_address: str
    owner_address: str
    spender_address: str
    token_name: str
    token_symbol: str
    amount: int
    transaction_hash: str


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
        "topics": [consts.APPROVAL_EVENT_TOPIC, get_topic_from_address(address)],
    }
    w3_filter = w3.eth.filter(filter_args)  # type: ignore
    # Take all of these logs in order, the thirds topic (index 2) is the
    #   recipient and the uint256 data is the amount of allowance
    return w3_filter.get_all_entries()


def get_spender_hex_address(approval: LogReceipt) -> str:
    address_as_topic = approval["topics"][
        consts.APPROVAL_EVENT_RECIPIENT_ADDRESS_TOPIC_INDEX
    ].hex()
    address_hex = address_as_topic[-consts.ETHEREUM_ADDRESS_HEX_LENGTH:]
    return f"0x{address_hex}"


def get_owner_hex_address(approval: LogReceipt) -> str:
    address_as_topic = approval["topics"][
        consts.APPROVAL_EVENT_SENDER_ADDRESS_TOPIC_INDEX
    ].hex()
    address_hex = address_as_topic[-consts.ETHEREUM_ADDRESS_HEX_LENGTH:]
    return f"0x{address_hex}"


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


def get_erc20_approval_data(approvals: List[LogReceipt]) -> List[Erc20ApprovalData]:
    approval_data = []
    for approval in approvals:
        # The data is an int in base-16 (hex), it is also the number
        # representing the amount approved in an ERC20 Approval event
        # We don't need to fear overflow or anything, python ints are
        # much larger than the size given to value (256 bytes)
        approved_value = get_amount_from_approval(approval)
        if not approved_value:
            # If there is no approved value it is very likely we stumbled across the Approval
            # event from ERC721 (NFT) which has the same signature (and thus the same topics
            # we are filtering for) but has instead of value a token ID for an NFT.
            continue
        # Get the contract used, remember the one emitting the approval event is the contract itself
        contract_address = approval["address"]
        contract = get_contract(contract_address)
        # Get its name and symbol, and the approved value
        token_name = contract.functions.name().call()
        token_symbol = contract.functions.symbol().call()
        owner_address = get_owner_hex_address(approval)
        spender_address = get_spender_hex_address(approval)
        approval_data.append(
            Erc20ApprovalData(
                contract_address=contract_address,
                owner_address=owner_address,
                spender_address=spender_address,
                token_name=token_name,
                token_symbol=token_symbol,
                amount=approved_value,
                transaction_hash=approval["transactionHash"].hex(),
            )
        )
    return approval_data
