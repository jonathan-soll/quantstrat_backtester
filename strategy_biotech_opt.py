# strategy_biotech_opt.py

from __future__ import print_function

import datetime
from datetime import date
from dateutil.relativedelta import relativedelta

import numpy as np
import pandas as pd
import statsmodels.api as sm

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from data import HistoricCSVDataHandler, AlphaVantage_HistoricCSVDataHandler
from execution import SimulatedExecutionHandler
from portfolio import Portfolio

class BiotechApprovalStrategy(Strategy):
    '''
    Performs a biotech approval strategy where you buy at the close
    the trading day after the approval and sell six months later.
    '''

    def __init__(self, bars, events, approvals_csv_dir):
        '''
        Initializes the Biotech approval strategy

        Parameters:
        bars - The DataHandler object that provides bar information
        events - The Event Queue object
        approvals_csv_dir - The path to the csv file that has the tickers and the approval dates
        '''
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events

        self.approvals_csv_dir = approvals_csv_dir
        self.approvals_data = pd.read_csv(approvals_csv_dir)
        self.approvals_data['catalyst_date'] = pd.to_datetime(self.approvals_data['catalyst_date'])

        # Set to True if a symbol is in the market
        self.bought = self._calculate_initial_bought()
        self.entry_signals = self._calculate_initial_entry_signals()
        self.exit_dates = {}

    def _calculate_initial_entry_signals(self):
        '''
        Creates a dict of 0's for each symbol.
        This will be updated with a '1' if the symbol is to be traded on the next bar
        '''
        entry_signal = {}
        for s in self.symbol_list:
            entry_signal[s] = 0
        return entry_signal

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
        Reacts to a MarketEvent object and for each symbol see if there is an approval on that date.
        If there is one, then buy the stock otherwise don't do anything.

        It does this by generating a SignalEvent object if there is an approval on the same date
        as the current bar

        Parameters:
        event - a MarketEvent object
        '''
        # print(bar_date)
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bar = self.bars.get_latest_bar_value(s, 'Adj_Close')
                bar_date = self.bars.get_latest_bar_datetime(s)

                if bar is not None:

                    symbol = s
                    dt = datetime.datetime.utcnow()
                    sig_dir = ''

                    # check if we have a buy signal from the previous bar, if we do, buy the stock
                    if self.entry_signals[s] == 1:
                        sig_dir = 'LONG'
                        signal = SignalEvent(strategy_id = 1, symbol = symbol, datetime = dt, signal_type = sig_dir, strength = 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'LONG'
                        self.entry_signals[s] = 0 # reset to no signal
                        self.exit_dates[s] = bar_date + relativedelta(months=+6)
                        # print('exit date: ' + str(self.exit_dates[s].date()))

                    # check if we're at or after the exit date
                    if self.bought[s] != 'OUT' and bar_date >= self.exit_dates[s]:
                        sig_dir = 'EXIT'
                        signal = SignalEvent(strategy_id = 1, symbol = symbol, datetime = dt, signal_type = sig_dir, strength = 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'OUT'
                        self.exit_dates[s] = None

                    # generate the buy signals
                    if self.bought[s] == 'OUT':
                        entry_result = self.approvals_data[(self.approvals_data['ticker'] == s) &
                             (pd.to_datetime(self.approvals_data['catalyst_date']) == pd.to_datetime(bar_date))]
                        if len(entry_result) > 0:
                            self.entry_signals[s] = 1



if __name__ == '__main__':
    csv_dir = r'C:\Users\jonat\Documents\Projects\Quantstrat\First_Backtester\Data\\' # r'C:\Users\jonat\Documents\Projects\Quantstrat\ATVI.csv'
    approvals_csv_dir = r'C:\Users\jonat\Documents\Projects\Quantstrat\First_Backtester\Data\Biotech_Approvals_1Week.csv'

    symbol_list = ['ADMP', 'AEZS', 'AGEN', 'AGN', 'DRRX', 'EXEL', 'NVO', 'NVS',
                    'OPK', 'VRTX', 'ABBV', 'ENTA', 'AGIO', 'ADMS', 'XENT'
                    , 'DERM', 'ONCE', 'NEOS', 'ACRS', 'DOVA'
                    ]
    initial_capital = 1000000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2017, 1, 1, 0, 0, 0)

    backtest = Backtest(
        csv_dir = csv_dir,
        symbol_list = symbol_list,
        initial_capital = initial_capital,
        heartbeat = heartbeat,
        start_date = start_date,
        data_handler = AlphaVantage_HistoricCSVDataHandler,
        execution_handler = SimulatedExecutionHandler,
        portfolio = Portfolio,
        strategy = BiotechApprovalStrategy,
        external_data_dir = approvals_csv_dir,
        strategy_title = 'Biotech Approval Basic Strategy:  Go long at close of day following approval, sell 6 months later.'
    )
    backtest.simulate_trading()
