from typing import Annotated, List
from fastapi import FastAPI, Query
from pyproval

app = FastAPI()


@app.get("/approvals/")
def get_approvals(address: Annotated[List[str] | None, Query()] = None):
    pass
