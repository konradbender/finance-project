# Do not import any other scripts bc they all import this one
from datetime import datetime, date
from enum import Enum

import random
from secured import aws as secured
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import relationship

Trador_Base = declarative_base()


stock_expiration_association_table = Table('stock_expiration', Trador_Base.metadata,
                                        Column('stock_id', Integer, ForeignKey('stock.id', ondelete="CASCADE")),
                                        Column('expiration_id', Integer, ForeignKey('expiration.id', ondelete="CASCADE")))


pw = secured.server_password
user = secured.server_user


# This is for our object definition. Noo api calls form here





class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"


class OptionTypes(str, Enum):
    CALL = "call"
    PUT = "put"


class Symbols(str, Enum):
    apple = "AAPL"
    exxon_mobil = "XOM"


class Security():
    pass


class Quote(Trador_Base):
    __tablename__= 'quote'

    # fields
    id = Column(Integer, primary_key=True)
    price = Column(Float)
    timestamp = Column(DateTime)
    currency = Column(String)

    # relations
    stock_id = Column(Integer, ForeignKey('stock.id'))
    stock = relationship('Stock', back_populates='quotes')


    option_id = Column(Integer, ForeignKey('option.id'))
    option = relationship('Option', back_populates='quotes')


    def __init__(self, price: float, timestamp: datetime, currency: Currency):
        self.price = price
        self.timestamp = timestamp
        self.currency = currency.value

    def __eq__(self, other):
        return self.timestamp == other.timestamp

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def __hash__(self):
        return hash(self.timestamp)


class Stock(Trador_Base):
    __tablename__ = "stock"

    # fields
    id = Column(Integer, primary_key=True,)
    isin = Column(String)
    symbol = Column(String)
    standard_deviation = Column(Float)
    std_timestamp = Column(DateTime)

    # relations
    options = relationship("Option", back_populates='underlying', cascade='expunge')

    quotes = relationship('Quote', back_populates='stock', lazy='joined', cascade='expunge',
                          order_by='Quote.timestamp')

    position = relationship('Position', back_populates='stock',  cascade_backrefs=False)



    expirations = relationship('Expiration',
                          secondary=stock_expiration_association_table,
                               backref='stocks', cascade_backrefs = False)

    def __init__(self, isin, symbol):
        if isin is None and symbol is None:
            raise(RuntimeError)
        #self.isin = isin
        self.symbol = symbol


    def __repr__(self):
        if self.symbol is None:
            return self.isin
        else:
            return self.symbol


class Option(Trador_Base,Security):
    __tablename__ = "option"

    # fields
    id = Column(Integer,primary_key=True)

    isin = Column(String, unique=True)
    type = Column(String)
    strike = Column(Float)
    currency = Column(String)

    #relations
    # one-to-many with bidirectional behavior
    underlying_id = Column(Integer, ForeignKey("stock.id"))
    underlying = relationship("Stock", back_populates="options")
    # one-to-many
    expiration_id = Column(Integer,ForeignKey('expiration.id', ondelete='SET NULL'))
    expiration = relationship('Expiration')
    # many-to-one
    quotes = relationship('Quote', back_populates='option', lazy='joined', order_by = 'Quote.timestamp')

    position = relationship('Position', back_populates='option')

    def __init__(self, isin: str, strike: float,
                     option_type: OptionTypes, currency: Currency = Currency.USD ):


        self.isin = isin
        self.strike = strike
        self.type = option_type
        if type(currency) is Currency:
            self.currency = currency.value
        else:
            self.currency = currency


    def __repr__(self):
       return self.isin

    def __eq__(self, other):
        return self.isin == other.isin

    def __hash__(self):
        return hash(self.isin)


class Position(Trador_Base):
    __tablename__ = 'position'

    id = Column(Integer,primary_key=True)
    multiple = Column(Float)

    stock_id = Column(Integer, ForeignKey('stock.id', ondelete='SET NULL'))
    stock = relationship('Stock', back_populates = 'position')

    option_id = Column(Integer, ForeignKey('option.id', ondelete='SET NULL'))
    option = relationship('Option', back_populates = 'position')

    ISIN = Column(String)

    buy_date = Column(DateTime)
    buy_price = Column(Float)

    sell_date = Column(DateTime)
    sell_price = Column(Float)

    def __init__(self,option,price,date):
        self.option = option
        self.ISIN = option.isin
        self.buy_price = price
        self.buy_date = date


    def sell(self,price,date):
        self.sell_date = price
        self.sell_date = date



class Expiration(Trador_Base):
    __tablename__ = "expiration"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, unique=True)
    options = relationship('Option', back_populates='expiration', cascade='all, delete')


    def __eq__(self, other):
        return self.date == other.date

    def __init__(self, date):
        self.date = date

    def __hash__(self):
        return hash(self.date)

    def __lt__(self, other):
        return self.date < other.date


class Activity(Trador_Base):
    __tablename__ = 'activity'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    closed_positions =  Column(Integer)
    new_positions = Column(Integer)
    analyzed_options = Column(Integer)
    more = Column(String)