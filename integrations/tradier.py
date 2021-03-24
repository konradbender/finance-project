from datetime import datetime

import requests
import secured.tradier as secured
from threading import Thread, Event
from backend import trador
from queue import Queue
base_url = "https://sandbox.tradier.com/"
version = "v1/"
my_token = secured.my_token
authorization = "Bearer " + my_token
seconds_between_requests = 1
date_format = '%Y-%m-%d'

class TradierGetter:

    def __init__(self, persistency = None, index = None):
        self.has_response = Event()
        self.index = index
        self.persistency = persistency
        self.response = None

class TradierQueue(Thread):

    def __init__(self, group = None, target = None, name = None, args = (), kwargs = {}, *, daemon = True):
        super().__init__(daemon=True)
        self.last_request = None
        self.queue = Queue()
        self.session = requests.Session()


    def run(self):
        while True:
            if not self.queue.empty():
                if not self.last_request is None:
                    while (self.last_request - datetime.now()).seconds < seconds_between_requests:
                        print("waited")
                        pass
                request, getter = self.queue.get()
                self.last_request = datetime.now()
                response = self.session.send(request)
                # print('response came in')
                response.raise_for_status()
                getter.response = response
                getter.has_response.set()
                # print('set response')




def get_expiration_dates(symbol):
    """
    Get a list of expiration dates on which options can be traded

    :param symbol: the symbol of the underlying
    :return: list of dates
    """

    response = requests.get(base_url + version + 'markets/options/expirations',
                            params={'symbol': symbol, 'includeAllRoots': 'true', 'strikes': 'false'},
                            headers={'Authorization': authorization, 'Accept': 'application/json'}
                            )
    response.raise_for_status()
    dates = response.json()["expirations"]["date"]
    for idx, date in enumerate(dates):
        dates[idx] = _make_date(date)

    return dates

    # TODO: With multiple symbols at once


def put_quotes_away(getter, engine):
    getter.has_response.wait()
    response = getter.response
    string_symbols, securities = getter.persistency
    response.raise_for_status()
    json_response = response.json()
    entries = json_response["quotes"]["quote"]
    quote_dicts = list()
    for entry in entries:
        assert type(entry) is dict
        return_symbol = entry['symbol']
        quote = entry['last']
        timestamp = _make_time(entry['trade_date'])
        if timestamp is None:
            raise RuntimeError('Timestamp is none!')
        currency = trador.Currency.USD
        if quote is None:
            continue
        quote_new = {'price': quote, 'timestamp': timestamp, 'currency': currency.value}
        try:
            index = string_symbols.index(return_symbol)
        except:
            raise RuntimeError(return_symbol + " did not return a quote!")
        if len(return_symbol) < 6:
            quote_new['stock_id'] = str(securities[index].id)
            quote_new['option_id'] = None
        else:
            quote_new['option_id'] = str(securities[index].id)
            quote_new['stock_id'] = None
        quote_dicts.append(quote_new)
    engine.execute(
        trador.Quote.__table__.insert(),
        quote_dicts
    )
    print("put all quotes in the list")
    return


def update_quotes(stock, queue, engine, batch_size=100) :
    securities = [stock]
    securities.extend(stock.options)
    string_symbols = str(securities)[1:-1].replace(' ', '')
    # make list
    string_symbols = string_symbols.split(',')
    quotes = [None]*len(securities)
    start = 0
    getters = list()
    symbols_for_request = list()
    while start < len(securities):
        if len(securities) > batch_size:
            symbols_for_request = str(securities[start:start + batch_size])
            start += batch_size
        else:
            symbols_for_request = str(securities)

            start = len(securities)
        string_for_request = symbols_for_request[1:-1]
        string_for_request = string_for_request.replace(' ', '')
        request = requests.Request('GET', base_url + version + "markets/quotes",
                                params={'symbols': string_for_request, "greeks": "false"},
                                headers={'Authorization': authorization, 'Accept': 'application/json'}
                            ).prepare()
        getter = TradierGetter(persistency=(string_symbols, securities))
        getters.append(getter)
        queue.queue.put((request,getter))
    threads = list()
    print("put off all requests")
    json_dicts = []
    for getter in getters:
        thread = Thread(target=put_quotes_away, args=[getter, engine])
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    print('here')
    print(len(quotes))
    # session.bulk_save_objects(quotes)
        ## populate security
    print('all are added')
    return







def get_option_chain(stock, expiration, request_queue):
    """
    Get a list of options, both call and put
    :param symbol: symbol of the underlying stock
    :param exp_date: exp date of the options
    :return: list of trador.Option elements
    """
    symbol = stock.symbol
    exp_date = expiration.date
    getter = TradierGetter()
    request = requests.Request('GET', base_url + version + "markets/options/chains",
                            params={'symbol': symbol, 'expiration': exp_date, 'greeks': 'false'},
                            headers={'Authorization': authorization, 'Accept': 'application/json'}
                            )
    request = request.prepare()
    request_queue.queue.put((request, getter))
    getter.has_response.wait()
    # print('getter has reponse')
    response = getter.response
    response.raise_for_status()
    json_response = response.json()
    options_raw = json_response["options"]["option"]


    # TODO: Time Zone!!
    # TODO: Now they expire at 0 o'clock but I think they expire at the ENDS of those days.
    expiration_date = _make_date(options_raw[0]["expiration_date"])

    options = []

    for option in options_raw:
        option_symbol = option["symbol"]

        strike = option["strike"]

        option_type = option["option_type"]
        last_price = option["last"]
        # TODO: This is no good with the time stamp manipluation
        last_timestamp = _make_time(option["trade_date"])

        if option_type == "call":
            option_type = trador.OptionTypes.CALL
        else:
            option_type = trador.OptionTypes.PUT
        option_new = {'isin': option_symbol, 'strike' : strike, 'type': option_type, 'currency': 'USD'}
        options.append(option_new)

    return options




def _make_time(time: int) -> datetime:
    """
    Get a correct time object from the string representation tradier uses

    :param time: int of the unix timestamp
    :return: datetime object
    """
    return datetime.fromtimestamp(time * 1e-3)


def _make_date(date: str) -> datetime:
    """
    Get a correct date object from the string representation tradier uses

    :param date: string of date
    :return: datetime object
    """
    return datetime.strptime(date, date_format)
