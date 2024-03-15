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
        return filtered_list[0]['symbol']


def check_if_currency_supported(currency_short_name: str) -> bool:
    all_vs_currencies = get_all_supported_vs_currencies()
    # They are all always lower case
    return currency_short_name.lower() in all_vs_currencies


def get_token_value_in_currency(token_symbol: str, currency_short_name: str) -> float:
    if not check_if_currency_supported(currency_short_name):
        raise CoinGeckoException("Unsupported VS currency")
    token_id = get_coingecko_token_id(token_symbol)
    if token_id is None:
        raise CoinGeckoException("Could not find related token ID")
    query_url = consts.COINGECKO_API_GET_TOKEN_PRICE_URL.format(ids=token_symbol, vs_curr=currency_short_name)
    result: Dict[str, Dict[str, float]] = requests.get(query_url).json()
    return result[token_id][currency_short_name]
