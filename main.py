from datetime import datetime

from flask import Flask
from sqlalchemy import desc

from persistency import setup_database
from backend.trador import Activity, Option, Stock

connection = setup_database.my_connection()
session = connection.session


def add_dummy():
    activity = Activity(date=datetime.now())
    session.add(activity)
    session.commit()


def print_status(arg):
    app = Flask('dummy')
    result = str()
    last_activation = session.query(Activity).order_by(desc(Activity.date)).limit(1).all()[-1]
    number_of_options = session.query(Option).count()
    stocks = session.query(Stock).all()
    options = {}
    for stock in stocks:
        # calls, puts
        options[stock.symbol] = [0, 0]
    statement_1 = "SELECT stock.symbol, COUNT(*) FROM option JOIN stock on stock.id = option.underlying_id WHERE option.type LIKE 'call' " \
                  "GROUP BY stock.id"
    calls = None
    with connection.engine.connect() as con:
        rs = con.execute(statement_1)
        for row in rs:
            symbol, number = row
            if number is None:
                number = 0
            options[symbol][0] = number
    statement_2 = "SELECT stock.symbol, COUNT(*) FROM option JOIN stock on stock.id = option.underlying_id WHERE option.type LIKE 'put' " \
                  "GROUP BY stock.id"
    puts = None
    with connection.engine.connect() as con:
        rs = con.execute(statement_2)
        for row in rs:
            symbol, number = row
            if number is None:
                number = 0
            options[symbol][1] = number

    result += "Welcome. This is the backend view on the Cloud Application from Konrad Bender <br/>"
    result += f"Currently, the program is watching {number_of_options} options. <br/>"
    time = str(last_activation.date)[:-3]
    result += "The last report was at " + time+" <br/><br/>"


    result += 'OVERVIEW OF OPTIONS DATABASE:<br/>'
    result += '======================<br/>'
    result += "<table> \
             <tr> \
               <th>Stock</th> \
               <th>Calls</th> \
               <th>Puts</th> " \
              "</tr> "

    for index, stock in enumerate(stocks):
        result += "<tr>"
        symbol = stock.symbol
        if len(symbol) < 3:
            symbol += " \t"
        calls = str(options[stock.symbol][0])
        if len(calls) < 3:
            calls += " \t"
        puts = str(options[stock.symbol][1])
        if len(puts) < 3:
            puts += " \t"
        result += f"<td>{symbol} </td> <td>" + calls + " </td> <td> " + puts + "</td>"
        result += "</tr>"

    result += "</table>"
    result += "<br/> <br/>"

    result += 'OVERVIEW OF PORTFOLIO:<br/>'
    result += '======================<br/>'
    statement_3 = "SELECT stock.symbol, COUNT(*), AVG(position.multiple) FROM position JOIN option on position.option_id = option.id " \
                  "JOIN stock on option.underlying_id = stock.id " \
                  "GROUP BY stock.id"
    result += "<table> \
         <tr> \
           <th>Stock</th> \
           <th>Options</th> \
           <th>Avg. Multiple</th> " \
              "</tr> "
    # result += "<br/>Stock\tOptions\t\tAvg. Multiple \r<br/>"

    with connection.engine.connect() as con:
        result += "<tr>"
        rs = con.execute(statement_3)
        for row in rs:
            symbol, number, average = row
            number = str(number)
            if len(symbol) == 3 or len(symbol) == 2:
                symbol += "\t"
            if len(number) < 4:
                number += "\t"
            result += f"<td>{symbol} </td> <td>" + number + " </td> <td> %.2f </td>" % average

            result += "</tr>"
    result += "</table>"
    result += "<br/><br/>"
    result += '<br/>Thank you. For more questions, reach out at <a href="http://konradbender.com"> www.konradbender.com </a>'
    activity = Activity(date=datetime.now())
    session.add(activity)
    session.commit()
    print('hello')
    print('second')
    return app.make_response(result)


print(print_status(None))
