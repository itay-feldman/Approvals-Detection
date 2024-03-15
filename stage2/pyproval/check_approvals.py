import click
from pyproval.utils import (
    filter_for_latest_approvals,
    get_erc20_approval_data,
    get_approval_events,
    is_valid_address,
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
    # Check if given address is valid
    if not is_valid_address(address):
        raise click.BadParameter("Invalid client address")
    # Call approval checker here
    all_approvals = get_approval_events(address)
    # Filter out redundant approvals
    latest_approvals = filter_for_latest_approvals(all_approvals)
    # Using the approval logs list, print everything here
    for approval in get_erc20_approval_data(latest_approvals):
        try:
            if show_spender:
                click.echo(
                    f"approval on {approval.token_name} ({approval.token_symbol}) of {approval.amount} "
                    f"to {hex(int(approval.spender_address, 16))}"
                )
            else:
                click.echo(
                    f"approval on {approval.token_name} ({approval.token_symbol}) of {approval.amount}"
                )
        except Exception as e:
            click.echo(
                f"Error occurred on approval event from transaction: {approval.transaction_hash}"
            )
            click.echo(e)


if __name__ == "__main__":
    check_approvals()
