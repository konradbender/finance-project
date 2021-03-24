from backend.trador import  Position, OptionTypes, Stock, Option, Expiration
from backend import parameters
from datetime import datetime
from threading import Thread
from persistency import setup_database
from integrations import fred
from numerical_methods import black_scholes
from math import ceil
from backend.refresh import refresh_standard_deviation

my_connection = setup_database.my_connection()
session = my_connection.session

class custom_worker(Thread):

    def __init__(self, target, args):
        super().__init__()
        self.target = target
        self.args = args
        self.result = None

    def run(self):
        self.result = self.target(*self.args)
        # print('custom worker has run')

def evaluate_and_buy_options(fetched_rates, standard_deviation, quote_stock, options, connection):
    max_multiple = 1 - parameters.desired_discount
    positions = list()
    for option in options:
        if not len(option.position) == 0:
            # we have already bought it.
            continue
        quote_option = None
        if len(option.quotes) > 0:
            quote_option = option.quotes[0]
        else:
            continue
        risk_free_rate = fred.get_discount_rate(datetime.now(), option.expiration.date, fetched_rates)
        value = None
        T = (option.expiration.date - datetime.now()).days / 365
        if option.type == OptionTypes.CALL:
            value = black_scholes.bs_call(option.strike, quote_stock.price, T,
                                          risk_free_rate, standard_deviation)
        else:
            value = black_scholes.bs_put(option.strike, quote_stock.price, T,
                                         risk_free_rate, standard_deviation)
        if quote_option.price < max_multiple*value:
            # print('that is a buy! Stock:' + option.underlying.symbol)
            position = {'option_id' : option.id, 'ISIN': option.isin, 'buy_date': datetime.now(),
                        'buy_price': quote_option.price, 'multiple': quote_option.price / value}
            # position = Position(option,quote_option.price,datetime.now())
            # session.add(position)
            positions.append(position)
    if len(positions) > 0:
        print('starting to add')
        connection.engine.execute(
            Position.__table__.insert(),
            positions
        )
    return


def evaluate_and_buy(stock, fetched_rates, number_of_threads, connection):
    options = stock.options
    if len(options) <= 0:
        raise RuntimeWarning('No options to evaluate for stock: ' + str(stock))
        return
    quote_stock = stock.quotes[0]
    # standard deviation is given in percent, make it base 10
    # standard_deviation = iex.get_standard_deviation(stock.symbol) * 1e-2
    standard_deviation = stock.standard_deviation
    positions = list()
    options_per_thread = int(len(options) / number_of_threads)
    print(options_per_thread)
    threads = list()
    start = 0
    while start + options_per_thread < len(options):
        end = start + options_per_thread
        thread = custom_worker(target=evaluate_and_buy_options, args = [fetched_rates, standard_deviation,
                                                                 quote_stock, options[start:end], connection])
        threads.append(thread)
        thread.start()
        start += options_per_thread
    thread = custom_worker(target=evaluate_and_buy_options, args=[fetched_rates, standard_deviation,
                                                           quote_stock, options[start: len(options), connection]])
    threads.append(thread)
    thread.start()
    print('set off all threads for ' + stock.symbol)
    for thread in threads:
        thread.join()

    return


def review_options():
    stocks = session.query(Stock).join(Option, Expiration).filter(Expiration.date >= datetime.now()).all()
    if (datetime.now() - stocks[0].std_timestamp).days > 14:
        refresh_standard_deviation()
    number_of_options = [len(stock.options) for stock in stocks]
    weights = [number / sum(number_of_options) for number in number_of_options]
    allowed_threads = [ceil(weight * parameters.max_number_of_threads) for weight in weights]
    rates = fred.Fetched_Rates()
    threads = []
    for index, stock in enumerate(stocks):
        number_of_threads =  allowed_threads[index]
        new_conn = setup_database.my_connection()
        thread = Thread(target=evaluate_and_buy, args=[stock, rates,number_of_threads,new_conn])
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    return

now = datetime.now()
review_options()
print('it took %.2f seconds' %(datetime.now() - now).seconds)