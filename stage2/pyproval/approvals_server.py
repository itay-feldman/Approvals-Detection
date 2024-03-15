import uvicorn
from web3 import Web3
from typing import Annotated, Dict, List
from fastapi import FastAPI, HTTPException, Response, Query
from pyproval.approval_utils import get_approval_events, is_valid_address, LogReceipt

app = FastAPI(debug=True)


@app.get("/approvals/")
def get_approvals(addresses: Annotated[List[str], Query()]):
    if any([not is_valid_address(address) for address in addresses]):
        raise HTTPException(400, "One or more of the account addresses supplied was invalid")
    response: Dict[str, List[LogReceipt]] = {}
    for address in addresses:
        response[address] = get_approval_events(address)
    # Return response
    return Response(content=Web3.to_json(response), media_type="application/json")


def main():
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
