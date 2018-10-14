from __future__ import print_function

import datetime

import numpy as np
import pandas as pd

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from data import HistoricCSVDataHandler
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

        self.bars = bars_list
        self.symbol_list = self.bars.symbol_list
        self.events = events

        self.bought = self._calculate_initial_bought()

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
                if self.bought[s] = 'Out':
                    print('%s: LONG %s' % (bar_date, s))

if __name__ == '__main__':
    symbol_list = ['AAPL', 'MSFT']
    initial_capital = 1000000
    heartbeat = 0.0
    start_date = datetime.datetime(2017, 1, 1, 0, 0, 0)

    backtest = Backtest(
    
    )
