# data.py

from __future__ import print_function

from abc import ABCMeta, abstractmethod
import datetime
import os, os.path

import numpy as np
import pandas as pd

from event import MarketEvent

class DataHandler(object):
    '''
    An abstract base class providing an interface for all subsequent (inherited) data handlers (both live and historiacal)

    The goal of a (derived) DataHandler object is to output a generated set of bars (OHLCVI) for each symbol requested.

    This replicates how live trading functions to ensure realistic backtesting
    '''

    # lets Python know this is an Abtract Base Class, which means it can't be instantiated directly
    # only inheritants of the class (subclasses) can be instantiated
    __metaclass__ = ABCMeta

    @abstractmethod # lets Python know that the method will be overridden in subclasses
    def get_latest_bar(self, symbol, N=1):
        '''
        Returns the last bar updated
        '''
        raise NotImplementedError('Should implement get_latest_bar()')

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        '''
        Returns the last N bars updated
        '''
        raise NotImplementedError('Should implement get_latest_bars()')

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        '''
        Returns a Python datetime object for the latest bar
        '''
        raise NotImplementedError('Should implement get_latest_bar_datetime()')

    @abstractmethod
    def get_latest_bar_value(self, symbol, val_type):
        '''
        Returns one of the Open, High, Low, Close, Volume or OI from the last bar
        '''
        raise NotImplementedError('Should implement get_latest_bar_value()')

    @abstractmethod
    def get_latest_bar_values(self, symbol, val_type):
        '''
        Returns the last N bar values from the latest_symbol list of N-k if less available
        '''
        raise NotImplementedError('Should implement get_latest_bar_values()')

    @abstractmethod
    def update_bars(self):
        '''
        Pushes the latest bars to the bars_queue for each symbol in a tupe OHLCVI format
        '''
        raise NotImplementedError('Should implement update_bars()')


class HistoricCSVDataHandler(DataHandler):
    '''
    This DataHandler subclass is designed to reach CSV files for each requested symbol from the disk and
    provide an interface to obtain the 'latest' bar in a simulation of a live trading interface
    '''

    def __init__(self, events, csv_dir, symbol_list):
        '''
        Initializes the DataHandler by getting the location of the csv files (csv_dir) and a list of symbols to track.

        It assumes all the files are named 'symbol.csv' where 'symbol' is a string in the symbol_list

        Parameters:
        events - The Event Queue
        csv_dir - Absolute directory path to the csv files
        symbol_list - A list of symbol strings
        '''

        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True

        self._open_convert_csv_files()

    def _open_convert_csv_files(self):
        '''
        Opens the CSV files from the data directory, converting them into pandas row iterables within a symbol dictionary
        This handler assumes the data was taken from my database using the following query and then copied into a CSV file
        with the name <<symbol>>.csv.

        SELECT
            p.price_date
            , p.open_price
            , p.high_price
            , p.low_price
            , p.close_price
            , p.adj_close_price
            , p.volume
        FROM dbo.daily_price p
        JOIN dbo.symbol s ON p.symbol_id = s.id
        WHERE
            ticker = 'ATVI'
        order by price_date
        '''

        comb_index = None
        for s in self.symbol_list: # for each and every symbol we care about
            # load the csv file with no head information, indexed on the date
            self.symbol_data[s] = pd.io.parsers.read_csv(
                os.path.join(self.csv_dir, '%s.csv' % s),
                header = 0, index_col = 0, parse_dates = True,
                names = [
                    'price_date',
                    'open_price',
                    'high_price',
                    'low_price',
                    'close_price',
                    'adj_close_price',
                    'volume'
                ]
            ).sort_values(by = 'price_date')   # .sort()

            # combine the index to pad forward values
            if comb_index is None: # if it's the first symbol, set the index to the dates of the first symbol
                comb_index = self.symbol_data[s].index
            else: # if it's not the first symbol, combine the dates of all of the symbols
                comb_index.union(self.symbol_data[s].index)

            # set the latest symbol data to None
            self.latest_symbol_data[s] = []

        # Reindex the dataframes
        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method = 'pad').iterrows()

    def _get_new_bar(self, symbol):
        '''
        Returns the latest bar from the data feed.
        '''
        for b in self.symbol_data[symbol]:
            yield b # return a new bar but don't store it in memory, (return it and then throw it away)

    def get_latest_bar(self, symbol):
        '''
        Returns the last bar from the latest_symbol list
        '''
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print('That symbol is not in the historical data set.')
            raise
        else:
            return bars_list[-1]

    def get_latest_bars(self, symbol, N=1):
        '''
        Returns the last N bars from the latest_symbol list,
        or N-k if less available
        '''
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print('That symbol is not in the historical data set.')
            raise
        else:
            return bars_list[-N:]

    def get_latest_bar_datetime(self, symbol):
        '''
        Returns a python datetime object for the last bar
        '''
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print('That symbol is not in the historical data set.')
            raise
        else:
            return bars_list[-1][0]

    def get_latest_bar_value(self, symbol, val_type):
        '''
        Returns one of the Open, High, Low, Close, Volume or OI values from the pandas bar series object
        '''
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print('That symbol is not available in the historical data set.')
            raise
        else:
            return getattr(bars_list[-1][1], val_type)

    def get_latest_bars_values(self, symbol, val_type, N=1):
        '''
        Returns one of the Open, High, Low, Close, Volume or OI values from the pandas bar series object
        for the last N bars or N-k if available
        '''
        try:
            bars_list = self.get_latest_bars(symbol, N)
        except KeyError:
            print('That symbol is not available in the historical data set.')
            raise
        else:
            return np.array([getattr(b[1], val_type) for b in bars_list])

    def update_bars(self):
        '''
        Pushes the latest bar to the latest_symbol_data structure for all symbols in the symbol list
        '''

        for s in self.symbol_list:
            try:
                bar = next(self._get_new_bar(s)) # grab the new bar
            except StopIteration:
                self.continue_backtest = False # of there is no next bar then the backtest is over
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar) # tack the next bar onto the latest_symbol_data
        self.events.put(MarketEvent())


class AlphaVantage_HistoricCSVDataHandler(DataHandler):
    '''
    This DataHandler subclass is designed to reach CSV files for each requested symbol from the disk and
    provide an interface to obtain the 'latest' bar in a simulation of a live trading interface
    '''

    def __init__(self, events, csv_dir, symbol_list):
        '''
        Initializes the DataHandler by getting the location of the csv files (csv_dir) and a list of symbols to track.

        It assumes all the files are named 'symbol.csv' where 'symbol' is a string in the symbol_list

        Parameters:
        events - The Event Queue
        csv_dir - Absolute directory path to the csv files
        symbol_list - A list of symbol strings
        '''

        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True

        self._open_convert_csv_files()

    def _open_convert_csv_files(self):
        '''
        Opens the CSV files from the data directory, converting them into pandas row iterables within a symbol dictionary
        This handler assumes the data was taken from my database using the following query and then copied into a CSV file
        with the name <<symbol>>.csv.

        SELECT
        	[Date],
        	[Adj_Close]
        from dbo.alphavantage_daily_data b
        where b.ticker = 'abbv'
        '''

        comb_index = None
        for s in self.symbol_list: # for each and every symbol we care about
            # load the csv file with no head information, indexed on the date
            
            self.symbol_data[s] = pd.io.parsers.read_csv(
                os.path.join(self.csv_dir, '%s.csv' % s),
                header = 0, index_col = 0, parse_dates = True,
                names = [
                    'Date',
                    'Adj_Close',
                ]
            ).sort_values(by = 'Date')   # .sort()

            # combine the index to pad forward values
            if comb_index is None: # if it's the first symbol, set the index to the dates of the first symbol
                comb_index = self.symbol_data[s].index
            else: # if it's not the first symbol, combine the dates of all of the symbols
                comb_index.union(self.symbol_data[s].index)

            # set the latest symbol data to None
            self.latest_symbol_data[s] = []

        # Reindex the dataframes
        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method = 'pad').iterrows()

    def _get_new_bar(self, symbol):
        '''
        Returns the latest bar from the data feed.
        '''
        for b in self.symbol_data[symbol]:
            yield b # return a new bar but don't store it in memory, (return it and then throw it away)

    def get_latest_bar(self, symbol):
        '''
        Returns the last bar from the latest_symbol list
        '''
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print('That symbol is not in the historical data set.')
            raise
        else:
            return bars_list[-1]

    def get_latest_bars(self, symbol, N=1):
        '''
        Returns the last N bars from the latest_symbol list,
        or N-k if less available
        '''
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print('That symbol is not in the historical data set.')
            raise
        else:
            return bars_list[-N:]

    def get_latest_bar_datetime(self, symbol):
        '''
        Returns a python datetime object for the last bar
        '''
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print('That symbol is not in the historical data set.')
            raise
        else:
            return bars_list[-1][0]

    def get_latest_bar_value(self, symbol, val_type):
        '''
        Returns one of the Open, High, Low, Close, Volume or OI values from the pandas bar series object
        '''
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print('That symbol is not available in the historical data set.')
            raise
        else:
            return getattr(bars_list[-1][1], val_type)

    def get_latest_bars_values(self, symbol, val_type, N=1):
        '''
        Returns one of the Open, High, Low, Close, Volume or OI values from the pandas bar series object
        for the last N bars or N-k if available
        '''
        try:
            bars_list = self.get_latest_bars(symbol, N)
        except KeyError:
            print('That symbol is not available in the historical data set.')
            raise
        else:
            return np.array([getattr(b[1], val_type) for b in bars_list])

    def update_bars(self):
        '''
        Pushes the latest bar to the latest_symbol_data structure for all symbols in the symbol list
        '''

        for s in self.symbol_list:
            try:
                bar = next(self._get_new_bar(s)) # grab the new bar
            except StopIteration:
                self.continue_backtest = False # of there is no next bar then the backtest is over
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar) # tack the next bar onto the latest_symbol_data
        self.events.put(MarketEvent())
