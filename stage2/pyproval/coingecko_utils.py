import requests
from pyproval import consts
from typing import Dict, List, Optional


class CoinGeckoException(Exception):
    pass


def _list_coins() -> List[Dict[str, str]]:
    response = requests.get(consts.COINGECKO_API_LIST_ALL_COINS_URL)
    if response.ok:
        return response.json()
    else:
        raise CoinGeckoException(f"Coin Gecko responded with an error: {response.text}")


# Holding a list like this saves us the request to update (coin gecko will often throttle us)
# but it could possible make the coin list outdated, since this is an exercise, I think that's fine
_COIN_GECKO_LIST = _list_coins()


def get_coingecko_id_from_name(token_name: str) -> Optional[str]:
    filtered_list = list(
        filter(lambda item: item["name"] == token_name, _COIN_GECKO_LIST)
    )
    if filtered_list:
        # First result takes priority
        return filtered_list[0]["id"]


def get_all_supported_vs_currencies() -> List[str]:
    response = requests.get(consts.COINGECKO_API_LIST_VS_CURRENCIES_URL)
    return response.json()


def get_token_value_in_currency(token_name: str, currency_short_name: str) -> float:
    token_id = get_coingecko_id_from_name(token_name)
    if token_id is None:
        raise CoinGeckoException("Could not find related token ID")
    query_url = consts.COINGECKO_API_GET_TOKEN_PRICE_URL.format(
        ids=token_id, vs_curr=currency_short_name
    )
    response = requests.get(query_url)
    if not response.ok:
        raise CoinGeckoException(f"Coin Gecko responded with an error: {response.text}")
    result: Dict[str, Dict[str, float]] = response.json()
    return result[token_id][currency_short_name]
