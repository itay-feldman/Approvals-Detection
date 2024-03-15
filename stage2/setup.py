from setuptools import find_packages, setup
from pyproval import __version__


setup(
    name="PyProval",
    version=__version__,
    packages=find_packages(),
    description="Somewhat quick and dirty script to show all of the Approval (ERC20-like) "
    "events for an Ethereum account address",
    requires=["click", "fastapi", "pydantic", "uvicorn", "web3py"],
    entry_points={
        "console_scripts": [
            "check_approvals=pyproval.check_approvals:check_approvals",
            "approvals_server=pyproval.approvals_server:main",
        ]
    },
)
