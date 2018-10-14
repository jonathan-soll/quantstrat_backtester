# backtest.py

from __future__ import print_function
import datetime
import pprint

try:
    import Queue as queue
except ImportError:
    import queue

import time
from backtest_base import Backtest_Base

class Backtest(Backtest_Base):
    '''
    Encapsulates the settings and components for carrying out an event-driven backtest
    '''

    def __init__(
        self, csv_dir, symbol_list, initial_capital,
        heartbeat, start_date, data_handler,
        execution_handler, portfolio, strategy,
        strategy_title, external_data_dir
    ):
        '''
        Initializes the backtest with the path to the historical data, the list of symbols to be traded, the initial capital,
        the heartbeat time (in milliseconds), the start date of the backtest, the DataHandler object,
        the ExecutionHandler object, the Portfolio object, and the Strategy object.

        A Queue is used to hold the events.

        Parameters:
        csv_dir - The hard root to the CSV data directory
        symbol_list - The list of symbol strings
        initial_capital - The starting capital for the portfolio
        heartbeat - The backtest "heartbeat" in seconds
        start_date - The start datetime of the strategy
        data_handler - (Class) Handles the market data feed
        execution_handler - (Class) Handles the orders/fills for trades
        portfolio - (Class) Keeps track of portfolio current and prior positions.
        strategy - (Class) Generates signals based on market data.
        external_data_dir - A path to a csv file containing external data for the strategy
        '''
        self.external_data_dir = external_data_dir
        Backtest_Base.__init__(self, csv_dir, symbol_list, initial_capital,
                                heartbeat, start_date, data_handler,
                                execution_handler, portfolio, strategy,
                                strategy_title)


    def _generate_trading_instances(self):
        '''
        Generates the trading instance objects from their class types
        This part is where we take the handler classes we passed in when we initialized
        the backtest and we initialize the actual objects to be used in the backtest.
        '''

        print('Creating DataHandler , Strategy, Portfolio and ExecutionHandler')
        self.data_handler = self.data_handler_cls(self.events, self.csv_dir, self.symbol_list)
        self.strategy = self.strategy_cls(self.data_handler, self.events, self.external_data_dir)
        self.portfolio = self.portfolio_cls(self.data_handler, self.events, self.start_date, self.initial_capital)
        self.execution_handler = self.execution_handler_cls(self.events)
