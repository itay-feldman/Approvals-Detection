import requests
from pyproval import consts
from typing import Dict, List, Optional


class CoinGeckoException(Exception):
    pass


def list_coins() -> List[Dict[str, str]]:
    response = requests.get(consts.COINGECKO_API_LIST_ALL_COINS_URL)
    if response.ok:
        return response.json()
    else:
        raise CoinGeckoException(f"Coin Gecko responded with an error: {response.text}")


def get_coingecko_id_from_symbol(token_symbol: str) -> Optional[str]:
    all_tokens = list_coins()
    filtered_list = list(
        filter(lambda item: item["symbol"].lower() == token_symbol.lower(), all_tokens)
    )
    if filtered_list:
        # First result takes priority
        return filtered_list[0]["id"]


def get_coingecko_id_from_name(token_name: str):
    # This is a simple way to get the coin gecko id for a token
    # Querying for the full list every time is time consuming and 
    # makes coin gecko block our request because we exceed our allowed rate
    return token_name.lower().replace(" ", "-")


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
