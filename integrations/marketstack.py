import requests
import secured.marketstack as secured
from backend.trador import Stock

key = secured.key

url = "http://api.marketstack.com"
version = "/v1"
endpoint = "/tickers"
batch_size = 1000


def get_tickers(exchange: str, max_batches = None):
    tickers = []
    n_of_returned = batch_size
    n_of_batch = 0
    while n_of_returned == batch_size and not (not max_batches is None and n_of_batch > max_batches):
        response = requests.get(url+version+endpoint,{"access_key" : key, "exchange":exchange, "limit": batch_size, "offset" : n_of_batch*n_of_returned})
        response.raise_for_status()
        response = response.json()
        n_of_returned = len(response['data'])
        n_of_batch += 1
        for entry in response['data']:
            stock = Stock(isin = None, symbol=entry['symbol'])
            tickers.append(stock)
    return tickers


