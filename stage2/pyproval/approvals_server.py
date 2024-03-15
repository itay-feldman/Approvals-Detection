import uvicorn
from typing import Annotated, Dict, List
from fastapi import FastAPI, HTTPException, Query
from pyproval.approval_utils import (
    filter_for_latest_approvals,
    get_erc20_approval_data,
    get_approval_events,
    is_valid_address,
    Erc20ApprovalData,
)

app = FastAPI(debug=True)


@app.get("/approvals/")
def get_approvals(addresses: Annotated[List[str], Query()]):
    if any([not is_valid_address(address) for address in addresses]):
        raise HTTPException(
            400, "One or more of the account addresses supplied was invalid"
        )
    response: Dict[str, List[Erc20ApprovalData]] = {}
    for address in addresses:
        approvals = get_approval_events(address)
        latest_approvals = filter_for_latest_approvals(approvals)
        response[address] = get_erc20_approval_data(latest_approvals)
    # Return response
    return response


def main():
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
