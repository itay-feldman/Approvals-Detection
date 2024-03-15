import click
from pyproval.approval_utils import (
    filter_for_latest_approvals,
    get_amount_from_approval,
    get_approval_events,
    get_contract,
    get_spender_hex_address,
)


@click.command("PyProval")
@click.option(
    "--address",
    type=str,
    required=True,
    help="Address of account to check approval history on",
)
@click.option(
    "--show-spender",
    is_flag=True,
    default=False,
    help="If specified, the spender address is also shown",
)
def check_approvals(address: str, show_spender: bool):
    # Call approval checker here
    all_approvals = get_approval_events(address)
    # Filter out redundant approvals
    latest_approvals = filter_for_latest_approvals(all_approvals)
    # Using the approval logs list, print everything here
    for approval in latest_approvals:
        try:
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
            contract = get_contract(approval["address"])
            # Get its name and symbol, and the approved value
            contract_name = contract.functions.name().call()
            contract_symbol = contract.functions.symbol().call()
            if show_spender:
                # Get the spender's address
                spender_address = get_spender_hex_address(approval)
                click.echo(
                    f"approval on {contract_name} ({contract_symbol}) of {approved_value} "
                    f"to {hex(int(spender_address, 16))}"
                )
            else:
                click.echo(
                    f"approval on {contract_name} ({contract_symbol}) of {approved_value}"
                )
        except Exception as e:
            click.echo(f'Error occurred on approval event from transaction: {approval["transactionHash"].hex()}')
            raise click.Abort() from e


if __name__ == "__main__":
    check_approvals()
