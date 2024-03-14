from setuptools import find_packages, setup
from pyproval import __version__


setup(
    name='PyProval',
    version=__version__,
    packages=find_packages(),
    requires=[
        "click",
        "web3py"
    ],
    entry_points={
        'console_scripts': [
            ""
        ]
    }
)
