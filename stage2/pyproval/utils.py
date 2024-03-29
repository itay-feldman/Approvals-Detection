from collections import OrderedDict
from pydantic import BaseModel
from typing import Dict, List, Optional
from web3 import Web3
from web3.exceptions import BadFunctionCallOutput
from web3.types import LogReceipt
from pyproval import consts
from pyproval.coingecko_utils import get_token_value_in_currency, CoinGeckoException


class Erc20ContractData(BaseModel):
    contract_address: str
    token_name: Optional[str]
    token_symbol: Optional[str]
    token_value_usd: Optional[float]
    decimals: int


class Erc20ApprovalData(BaseModel):
    contract_data: Erc20ContractData
    owner_address: str
    spender_address: str
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


def get_approval_events(
    address: str, contract: Optional[str] = None
) -> List[LogReceipt]:
    # Create w3 object
    w3 = get_web3()
    # Filter by topics, topic 0 is the event type, topic 1 is the owner
    filter_args = {
        "fromBlock": 0,
        "toBlock": "latest",
        "topics": [consts.APPROVAL_EVENT_TOPIC, get_topic_from_address(address)],
    }
    if contract is not None:
        filter_args["address"] = contract
    w3_filter = w3.eth.filter(filter_args)  # type: ignore
    # Take all of these logs in order, the thirds topic (index 2) is the
    #   recipient and the uint256 data is the amount of allowance
    return w3_filter.get_all_entries()


def get_spender_hex_address(approval: LogReceipt) -> str:
    address_as_topic = approval["topics"][
        consts.APPROVAL_EVENT_RECIPIENT_ADDRESS_TOPIC_INDEX
    ].hex()
    address_hex = address_as_topic[-consts.ETHEREUM_ADDRESS_HEX_LENGTH :]
    return f"0x{address_hex}"


def get_owner_hex_address(approval: LogReceipt) -> str:
    address_as_topic = approval["topics"][
        consts.APPROVAL_EVENT_SENDER_ADDRESS_TOPIC_INDEX
    ].hex()
    address_hex = address_as_topic[-consts.ETHEREUM_ADDRESS_HEX_LENGTH :]
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
    latest_approvals: OrderedDict[str, OrderedDict[str, LogReceipt]] = OrderedDict()
    for approval in approvals:
        # We use the hex representation of the "recipient topic" as the key
        recipient_address = get_spender_hex_address(approval)
        contract_address = approval["address"]
        # Since the list is ordered, we know that a value with the same recipient should always override
        # the previous value with the same recipient.
        if recipient_address in latest_approvals:
            latest_approvals[recipient_address][contract_address] = approval
        else:
            latest_approvals[recipient_address] = OrderedDict(
                {contract_address: approval}
            )
    all_recipients = latest_approvals.values()
    all_approvals = []
    for recipient in all_recipients:
        all_approvals.extend(list(recipient.values()))
    return all_approvals


def get_contract(contract_address):
    w3 = get_web3()
    return w3.eth.contract(contract_address, abi=consts.ERC20_CONTRACT_ABI)


def get_amount_from_approval(approval: LogReceipt) -> Optional[int]:
    data = approval["data"].hex().lower().strip("0x")
    if data:
        return int(data, 16)
    return None


def get_token_name(contract) -> Optional[str]:
    # There are tokens like the Maker token that think it's funny to break
    # the ABI of ERC20 and instead return bytes32 for the name and symbol
    # and not a string, this breaks things so we wrap the calls
    try:
        return contract.functions.name().call()
    except BadFunctionCallOutput:
        return None


def get_token_symbol(contract):
    try:
        return contract.functions.symbol().call()
    except BadFunctionCallOutput:
        return None


def get_contract_data_from_address(contract_address: str) -> Erc20ContractData:
    contract = get_contract(contract_address)
    token_name = get_token_name(contract)
    token_symbol = get_token_symbol(contract)
    try:
        token_value_usd = (
            get_token_value_in_currency(token_name, "usd") if token_name else None
        )
    except CoinGeckoException:
        token_value_usd = None
    token_decimals = contract.functions.decimals().call()
    return Erc20ContractData(
        contract_address=contract_address,
        token_name=token_name,
        token_symbol=token_symbol,
        token_value_usd=token_value_usd,
        decimals=token_decimals,
    )


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
        # Get its name and symbol, and the approved value
        owner_address = get_owner_hex_address(approval)
        spender_address = get_spender_hex_address(approval)
        contract_data = get_contract_data_from_address(
            contract_address=contract_address
        )
        approval_data.append(
            Erc20ApprovalData(
                contract_data=contract_data,
                owner_address=owner_address,
                spender_address=spender_address,
                amount=approved_value,
                transaction_hash=approval["transactionHash"].hex(),
            )
        )
    return approval_data


def get_user_allowance_per_contract(
    approvals: List[Erc20ApprovalData],
) -> Dict[str, int]:
    """Given a list of approvals, return a dict of the form {contract: exposure}. This list
    should be filtered to latest updates only, as in, for the same owner and same spender in the same
    contract, there should only be a single entry. It is assumed this list contains the events
    for a single owner. Note: here, unlike with approvals, we check for the actual allowance
    """
    owner = approvals[0].owner_address if approvals else None
    if owner is None:
        return {}  # Save us some trouble...
    contracts = set([approval.contract_data.contract_address for approval in approvals])
    contracts_and_spenders: Dict[str, List[str]] = {}
    total_allowance: Dict[str, int] = {}
    # Get all spenders in a contract
    for address in contracts:
        filtered_approvals = filter(
            lambda approval: approval.contract_data.contract_address == address,
            approvals,
        )
        contracts_and_spenders[address] = list(
            set([approval.spender_address for approval in filtered_approvals])
        )
    for contract in contracts:
        if contract not in total_allowance:
            total_allowance[contract] = 0
        w3_contract = get_contract(contract)
        for spender in contracts_and_spenders[contract]:
            owner_checksum = Web3.to_checksum_address(owner)
            spender_checksum = Web3.to_checksum_address(spender)
            total_allowance[contract] += w3_contract.functions.allowance(
                Web3.to_checksum_address(owner_checksum), spender_checksum
            ).call()
        # The approval amount can be more than uin256 once we add everything so if it is, we take the lower value
        total_allowance[contract] = min(
            total_allowance[contract], consts.UINT256_MAX_VAL
        )
    return total_allowance


def get_user_balance_per_contract(approvals: List[Erc20ApprovalData]) -> Dict[str, int]:
    """It is assumes that all approvals are of the same owner"""
    # If list is empty (which is weird but ok) we skip
    owner = approvals[0].owner_address if approvals else None
    if owner is None:
        return {}
    contracts = set([approval.contract_data.contract_address for approval in approvals])
    balances: Dict[str, int] = {}
    for contract in contracts:
        w3_contract = get_contract(contract)
        # As part of the ERC20 standard, balanceOf is a must have function
        balances[contract] = w3_contract.functions.balanceOf(
            Web3.to_checksum_address(owner)
        ).call()
    return balances


def get_contract_name_from_address(contract_address: str) -> str:
    contract_data = get_contract_data_from_address(contract_address=contract_address)
    if contract_data.token_name:
        return contract_data.token_name
    if contract_data.token_symbol:
        return contract_data.token_symbol
    return contract_data.contract_address


def get_user_exposure_per_contract(
    approvals: List[Erc20ApprovalData],
) -> Dict[str, int]:
    allowances = get_user_allowance_per_contract(approvals)
    balances = get_user_balance_per_contract(approvals)
    exposure: Dict[str, int] = {}
    for contract in balances.keys():
        exposure[contract] = min(balances[contract], allowances[contract])
    return exposure


def get_user_exposure_per_contract_in_usd(
    approvals: List[Erc20ApprovalData],
) -> Dict[str, float]:
    exposure_in_tokens = get_user_exposure_per_contract(approvals)
    exposure_in_usd: Dict[str, float] = {}
    for contract, amount in exposure_in_tokens.items():
        contract_data = get_contract_data_from_address(contract_address=contract)
        if not contract_data.token_value_usd:
            raise Exception("Could not find conversion for USD")
        adjusted_amount = amount / (10**contract_data.decimals)
        exposure_in_usd[contract] = adjusted_amount * contract_data.token_value_usd
    return exposure_in_usd
