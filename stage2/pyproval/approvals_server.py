import uvicorn
from typing import Annotated, Dict, List
from fastapi import FastAPI, HTTPException, Query
from pyproval.utils import (
    filter_for_latest_approvals,
    get_erc20_approval_data,
    get_approval_events,
    is_valid_address,
    get_user_exposure_per_contract,
    Erc20ApprovalData,
)
import logging
logging.getLogger().setLevel(logging.INFO)

app = FastAPI(debug=True)


def _validated_addresses(addresses: List[str]):
    if any([not is_valid_address(address) for address in addresses]):
        raise HTTPException(
            400, "One or more of the account addresses supplied was invalid"
        )


@app.get("/approvals")
def get_approvals(addresses: Annotated[List[str], Query()]):
    _validated_addresses(addresses)
    response: Dict[str, List[Erc20ApprovalData]] = {}
    for address in addresses:
        approvals = get_approval_events(address)
        latest_approvals = filter_for_latest_approvals(approvals)
        response[address] = get_erc20_approval_data(latest_approvals)
    # Return response
    return response


@app.get("/exposure")
def get_exposure(addresses: Annotated[List[str], Query()], contract: Annotated[str, Query()]):
    _validated_addresses(addresses)
    result: Dict[str, Dict[str, int]] = {}
    for address in addresses:
        approvals = get_approval_events(address, contract=contract)
        latest_approvals = filter_for_latest_approvals(approvals)
        erc20_approvals = get_erc20_approval_data(latest_approvals)
        # The result should have only a single contract
        exposure = get_user_exposure_per_contract(erc20_approvals)
        result[address] = exposure
    return result


def main():
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
