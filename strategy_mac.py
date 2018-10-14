# mac.py

from __future__ import print_function

import datetime

import numpy as np
import pandas as pd
import statsmodels.api as sm

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from data import HistoricCSVDataHandler
from execution import SimulatedExecutionHandler
from portfolio import Portfolio

class MovingAverageCrossStrategy(Strategy):
    '''
    Performs a basic Moving Average Crossover strategy with a
    shorty/long simply weighted moving average. Default short/long
    windows are 100/400 periods respectively.
    '''

    def __init__(self, bars, events, short_window = 100, long_window = 400):
        '''
        Initializes the Moving Average Cross Strategy

        Parameters:
        bars - The DataHandler object that provides bar information
        events - The Event Queue object
        short_window - The short moving average lookback period
        long_window - The long moving average lookback period
        '''
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.short_window = short_window
        self.long_window = long_window

        # Set to True if a symbol is in the market
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
        '''
        Reacts to a MarketEvent object and for each symbol obtains the
        latest N bar closing prices where N is the larger lookback period.
        Then it calculates the simple moving averages. If the short SMA
        exceeds the long SMA, go long. If the long SMA exceeds the short SMA,
        exit the position.

        It does this by generating a SignalEvent object if there is a moving average cross
        and updating the "bought" attribute of the symbol to be 'LONG' or 'OUT'

        Parameters:
        event - a MarketEvent object
        '''
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars_values(s, 'adj_close_price', N=self.long_window)
                bar_date = self.bars.get_latest_bar_datetime(s)
                if bars is not None and bars != []:
                    short_sma = np.mean(bars[-self.short_window:])
                    long_sma = np.mean(bars[-self.long_window:])

                    symbol = s
                    dt = datetime.datetime.utcnow()
                    sig_dir = ''

                    if short_sma > long_sma and self.bought[s] == 'OUT':
                        print('LONG: %s' % bar_date)
                        sig_dir = 'LONG'
                        signal = SignalEvent(strategy_id = 1, symbol = symbol, datetime = dt, signal_type = sig_dir, strength = 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'LONG'


if __name__ == '__main__':
    csv_dir = r'C:\Users\jonat\Documents\Projects\Quantstrat\Data\\' #r'C:\Users\jonat\Documents\Projects\Quantstrat\ATVI.csv'

    symbol_list = ['ATVI']
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2000, 1, 1, 0, 0, 0)

    backtest = Backtest(
        csv_dir = csv_dir,
        symbol_list = symbol_list,
        initial_capital = initial_capital,
        heartbeat = heartbeat,
        start_date = start_date,
        data_handler = HistoricCSVDataHandler,
        execution_handler = SimulatedExecutionHandler,
        portfolio = Portfolio,
        strategy = MovingAverageCrossStrategy
    )
    backtest.simulate_trading()
