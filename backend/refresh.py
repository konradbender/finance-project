from backend.trador import *
import integrations.tradier as tradier
from persistency import setup_database
#import numerical_methods.black_scholes as black_scholes
from threading import Thread
from datetime import date
from sqlalchemy import desc

connection = setup_database.my_connection()
global_session = connection.session
engine = connection.engine
max_number_of_connections = 20


todays_date = datetime.now().date()


class custom_worker(Thread):

    def __init__(self, target, args):
        super().__init__()
        self.target = target
        self.args = args
        self.result = None

    def run(self):
        self.result = self.target(*self.args)
        # print('custom worker has run')

def refresh_expiration_dates(limit = None):
    # if limit is specified then it will only refresh for the top <limit> stocks in DB
    stocks = global_session.query(Stock).limit(limit).all()
    for stock in stocks:
        dates = tradier.get_expiration_dates(stock.symbol)
        for idx, date in enumerate(dates):
            date_query = global_session.query(Expiration).filter(Expiration.date==date).all()
            if len(date_query) == 0:
                dates[idx] = Expiration(date = date)
                global_session.add(dates[idx])
            else:
                dates[idx] = date_query[0]
        new_dates = set(dates)-set(stock.expirations)
        try:
            stock.expirations.extend(new_dates)
        except:
            raise (RuntimeError)
    global_session.commit()
    return



def filter_and_add(chain,expiration,stock, filter):
    new_options = list()
    options = list()
    if filter:
        for option in chain:
            values = list(option.values())
            # values.append(Currency.USD)
            options.append(Option(*values))
        new_options = set(options) - set(expiration.options)
        for option in new_options:
            option.expiration = expiration
            option.underlying = stock
            global_session.add(option)
        return None
    else:
        for option in chain:
            option['underlying_id'] = stock.id
            option['expiration_id'] = expiration.id
            new_options.append(option)
        return new_options

def bulk_insert(options):
    print('adding thread started')
    engine.execute(
        Option.__table__.insert(),
        options
    )

def refresh_options(limit = None, session = global_session, filter = True):
    # only the stocks for which we have found expiration dates
    stocks = session.query(Stock).join(Expiration, Stock.expirations).filter(Expiration.date >= datetime.now())\
        .limit(limit).all()
    threads = list()
    queue = tradier.TradierQueue()
    queue.start()
    for stock in stocks:
        result = session.query(Expiration).join(Option,Stock).order_by(desc(Expiration.date)).limit(1).all()
        max_date = None
        if len(result) > 0:
            max_date = result[0]
        for expiration in stock.expirations:
            if max_date is None or expiration.date > max_date.date:
                thread = custom_worker(target=tradier.get_option_chain, args=[stock, expiration, queue])
                thread.start()
                threads.append((thread,expiration,stock))
    # print('all threads started')
    new_options = list()
    second_threads = list()
    for thread, expiration, stock in threads:
        thread.join()
        chain = thread.result
        new_thread = custom_worker(target=filter_and_add, args=[chain,expiration,stock, filter])
        second_threads.append(new_thread)
        new_thread.start()
    # print('filter threads started')
    for thread in second_threads:
        thread.join()
        if thread.result is not None:
            new_options.extend(thread.result)
    if not filter:
        start = 0
        options_per_thread = int(len(new_options)/max_number_of_connections)
        n_of_options = len(new_options)
        adding_threads = list()
        while start + options_per_thread < n_of_options:
            thread = Thread(target=bulk_insert, args=[new_options[start:start+options_per_thread]])
            start += options_per_thread
            thread.start()
            adding_threads.append(thread)
        thread = Thread(target = bulk_insert, args=[new_options[start:n_of_options]])
        thread.start()
        adding_threads.append(thread)
        for thread in adding_threads:
            thread.join()
        print('finished insertion')
    if filter:
        global_session.commit()
    return



def refresh_quotes():
    stocks = global_session.query(Stock).join(Option, Expiration).filter(Expiration.date >= datetime.now()).all()
    queue = tradier.TradierQueue()
    queue.start()
    threads = list()
    for stock in stocks:
        # thread_stock = thread_session.query(Stock).filter(Stock.symbol == stock.symbol).all()[0]
        thread = custom_worker(target=tradier.update_quotes, args = [stock, queue, engine])
        thread.start()
        # thread.join()
        threads.append((thread, engine))
    for thread, session in threads:
        pass
        thread.join()
        # session.commit()
    print('starting commit')
    return



def close_positions(update_quotes = True):
    if update_quotes:
        refresh_quotes()
    sell_time = datetime.now()
    expired_positions = global_session.query(Position).join(Option, Expiration).filter(Expiration.date < datetime.now()).all()
    for position in expired_positions:
        sell_price = max(sorted(position.option.underlying.quotes)[0].price - position.option.strike,0)
        position.sell_price = sell_price
        position.sell_date = sell_time
    global_session.commit()

    return

def refresh_standard_deviation():
    stocks = global_session.query(Stock).all()
    for stock in stocks:
        std = iex.get_standard_deviation(stock.symbol)
        stock.standard_deviation = std
        stock.std_timestamp = datetime.now()
    global_session.commit()


print("Start: " + str(datetime.now()))
#refresh_expiration_dates()
print("expiration dates done: " + str(datetime.now()))
# refresh_options(filter = True)
print("options refreshed " + str(datetime.now()))
#refresh_quotes()
print("quotes refreshed " + str(datetime.now()))
#close_positions(False)
print("positions closed: " + str(datetime.now()))
#refresh_standard_deviation()


