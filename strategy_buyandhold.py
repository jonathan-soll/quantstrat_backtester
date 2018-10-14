from __future__ import print_function

import datetime

import numpy as np
import pandas as pd
import pyodbc

from strategy import Strategy
from event import SignalEvent
from backtest_sql import Backtest_SQL
from data import SimFinSQLDataHandler
from execution import SimulatedExecutionHandler
from portfolio import Portfolio

class BuyAndHoldStrategy(Strategy):
    """
    Performs a basic buy and hold strategy with a set of symbols
    """

    def __init__(self, bars, events):
        """
        Initializes the buy and hold strategy

        Parameters:
        bars - The DataHandler object that provides bar information
        events - The Event Queue object
        """

        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events

        self.bought = self._calculate_initial_bought()
        print(self.bought)

    def _calculate_initial_bought(self):
        '''
        Adds keys to the bought dictionary for all symbols and
        sets them to 'OUT'. Essentially tells the program we don't
        have a position in all of our symbls.
        '''
        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'
        return bought

    def calculate_signals(self, event):
        """
        Reacts to a MarketEvent object and for each symbol checks if there
        is currently a position, if there isn't, buy the stock, do nothing
        otherwise.
        """
        if event.type == 'Market':
            for s in self.symbol_list:
                bar_date = self.bars.get_latest_bar_datetime(s)
                if self.bought[s] == 'OUT':
                    print('%s: LONG %s' % (bar_date, s))
                    self.bought[s] = 'LONG'

if __name__ == '__main__':
    symbol_list = ['AAPL', 'MSFT']
    initial_capital = 1000000
    heartbeat = 0.0
    start_date = datetime.datetime(2017, 1, 1, 0, 0, 0)

    server = 'firstserverjs.database.windows.net'
    database = 'securities_master'
    username = 'JSoll'
    password = 'Emjosa139'
    driver= '{ODBC Driver 17 for SQL Server}'
    conn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)

    backtest = Backtest_SQL(
        symbol_list = symbol_list,
        initial_capital = initial_capital,
        heartbeat = heartbeat,
        start_date = start_date,
        data_handler = SimFinSQLDataHandler,
        execution_handler = SimulatedExecutionHandler,
        portfolio = Portfolio,
        strategy = BuyAndHoldStrategy,
        strategy_title = 'Buy and Hold',
        sqlconn = conn
    )
    backtest.simulate_trading()
