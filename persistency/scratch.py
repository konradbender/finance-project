from persistency import setup_database
import integrations.marketstack as marketstack

connection = setup_database.my_connection()
session = connection.session


def populate():
    stocks = marketstack.get_tickers('XNAS')
    #with open('data/tickers.txt') as f:
    #    csv_reader = csv.reader(f,delimiter=',')
    #    for row in csv_reader:
    #        stocks += row
    #for idx, stock in enumerate(stocks):
    #    if idx > 10:
    #        break
    #    stock = Stock(isin = None, symbol=stock)
    #    session.add(stock)
    #print(stocks)

    session.add_all(stocks[0:10])
    session.commit()





populate()

#stocks = session.query(Stock).all()
#print(len(stocks))
#print(stocks)


print("end of program")


