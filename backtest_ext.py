# backtest_ext.py

from __future__ import print_function
import datetime
import pprint

try:
    import Queue as queue
except ImportError:
    import queue

import time
from backtest import Backtest

class Backtest_Ext(Backtest):
    '''
    Encapsulates the settings and components for carrying out an event-driven backtest,
    inherits from the Backtest base class and allows for strategies that use external data
    '''

    def __init__(
        self, symbol_list, initial_capital,
        heartbeat, start_date, data_handler,
        execution_handler, portfolio, strategy,
        strategy_title, csv_dir, external_data_dir
    ):
        '''
        Inherits from Backtest and adds in the 'external_data_dir' parameter
        for handling signals generated in another csv file.

        Parameters:
        external_data_dir - A path to a csv file containing external data for the strategy
        '''
        self.csv_dir = csv_dir
        self.external_data_dir = external_data_dir
        Backtest.__init__(self, symbol_list, initial_capital,
                                heartbeat, start_date, data_handler,
                                execution_handler, portfolio, strategy,
                                strategy_title)


    def _generate_trading_instances(self):
        print('Creating DataHandler , Strategy, Portfolio and ExecutionHandler')
        self.data_handler = self.data_handler_cls(self.events, self.csv_dir, self.symbol_list)
        self.strategy = self.strategy_cls(self.data_handler, self.events, self.external_data_dir)
        self.portfolio = self.portfolio_cls(self.data_handler, self.events, self.start_date, self.initial_capital)
        self.execution_handler = self.execution_handler_cls(self.events)
