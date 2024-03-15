import requests
from pyproval import consts
from typing import Dict, List, Optional


class CoinGeckoException(Exception):
    pass


def list_coins() -> List[Dict[str, str]]:
    response = requests.get(consts.COINGECKO_API_LIST_ALL_COINS_URL)
    return response.json()


def get_all_supported_vs_currencies() -> List[str]:
    response = requests.get(consts.COINGECKO_API_LIST_VS_CURRENCIES_URL)
    return response.json()


def get_coingecko_token_id(token_symbol: str) -> Optional[str]:
    all_tokens = list_coins()
    filtered_list = list(filter(lambda item: item['symbol'].lower() == token_symbol.lower(), all_tokens))
    if filtered_list:
        # First result takes priority
        return filtered_list[0]['id']


def get_token_value_in_currency(token_symbol: str, currency_short_name: str) -> float:
    token_id = get_coingecko_token_id(token_symbol)
    if token_id is None:
        raise CoinGeckoException("Could not find related token ID")
    query_url = consts.COINGECKO_API_GET_TOKEN_PRICE_URL.format(ids=token_id, vs_curr=currency_short_name)
    result: Dict[str, Dict[str, float]] = requests.get(query_url).json()
    return result[token_id][currency_short_name]
