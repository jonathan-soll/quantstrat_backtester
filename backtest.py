# backtest.py

from __future__ import print_function
import datetime
import pprint

try:
    import Queue as queue
except ImportError:
    import queue

import time

class Backtest(object):
    '''
    Encapsulates the settings and components for carrying out an event-driven backtest
    '''

    def __init__(
        self, csv_dir, symbol_list, initial_capital, heartbeat, start_date, data_handler, execution_handler, portfolio, strategy,
        external_data_dir, strategy_title
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

        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date
        self.external_data_dir = external_data_dir
        self.strategy_title = strategy_title

        # we are actually passing in the class names of the handlers we want
        self.data_handler_cls = data_handler
        self.execution_handler_cls = execution_handler
        self.portfolio_cls = portfolio
        self.strategy_cls = strategy

        self.events = queue.Queue()

        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strats = 1

        self._generate_trading_instances()

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

    def _run_backtest(self):
        '''
        Executes the backtest

        For a...
            MarketEvent:  Strategy Object calculates new signals, Portfolio Object reindexes the time
            Signalevent:  Portfolio Object handles the signal and converts it to OrderEvents
            OrderEvent:   ExecutionHandler is sent the order and sends it to the broker
            FillEvent:    Portfolio updates according to the new positions
        '''
        i = 0
        while True:
            i += 1
            # print(i)
            # Update the market bars
            if self.data_handler.continue_backtest == True:
                self.data_handler.update_bars()
            else:
                break

            # Handle the events
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)

                        elif event.type == 'SIGNAL':
                            self.signals += 1
                            self.portfolio.update_signal(event)

                        elif event.type == 'ORDER':
                            self.orders += 1
                            self.execution_handler.execute_order(event)

                        elif event.type == 'FILL':
                            self.fills += 1
                            self.portfolio.update_fill(event)

            time.sleep(self.heartbeat)

    def _output_performance(self):
        '''
        Outputs the strategy performance from the backtest.
        '''
        self.portfolio.create_equity_curve_dataframe()

        print('Creating summary stats...')
        stats = self.portfolio.output_summary_stats(self.strategy_title)

        print('Creating equity curve...')
        print(self.portfolio.equity_curve.head(10))
        pprint.pprint(stats)

        print('Signals: %s' % self.signals)
        print('Orders: %s' % self.orders)
        print('Fills: %s' % self.fills)

        # print('Printing chart...')
        # self.portfolio.print_chart()

    def simulate_trading(self):
        '''
        Runs the backtest and outputs performance
        '''
        self._run_backtest()
        self._output_performance()