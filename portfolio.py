# portfolio.py

from __future__ import print_function

import datetime
from math import floor
try:
    import Queue as queue
except ImportError:
    import queue

import numpy as np
import pandas as pd

from event import FillEvent, OrderEvent
from performance import create_sharpe_ratio, create_drawdowns

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, FuncFormatter


class Portfolio(object):
    '''
    The Portfolio class handles the positions and market value of all instruments at a resolution of a 'bar'.
    The 'bar' can represent a period like second, minute, 5-minute, daily, etc.

    The positions DataFrame stores a time-index of the quantity of positions held.

    The holdings DataFrame stores the cash and market value of each symbol for each time-index. Also it contains
    the percentage change in portfolio value across bars.
    '''

    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        '''
        Initialises the portfolio with bars and an event queue.
        Also includes a starting datetime index and initial capital

        Parameters:
        bars - The DataHandler object with current market data
        events - The Event Queue object
        start_date - The start date (bar)  of the portfolio
        initial_capital - The starting capital
        '''
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list # the DataHandler object has a 'symbol_list' attribute
        self.start_date = start_date
        self.initial_capital = initial_capital

        self.all_positions = self.construct_all_positions()
        self.current_positions = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] ) # initialize a position of 0 for all symbols

        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

    def construct_all_positions(self):
        '''
        Constructs the positions list using the start_date to determine when the index will begin.

        Example with the following manually constructed symbol_list and start_date
        symbol_list = ['AAPL', 'GM.', 'TSLA']
        start_date = pd.to_datetime('1/1/2018')

        d = {'AAPL': 0, 'GM.': 0, 'TSLA': 0, 'datetime': Timestamp('2018-01-01 00:00:00')}
        d is returned in a list as [d] because it will be appended to over time to keep track of the positions across time
        '''
        d = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        d['datetime'] = self.start_date
        return [d]

    def construct_all_holdings(self):
        '''
        Constructs the holdings list using the start_date to determine when the index will begin.
        holdings are similar to the positions but there are extra keys to track cash on hand, total commissions paid,
        and total account equity. Short positions will be treated as negative.

        Starting cash and total account equity start out the same.

        Essentially there is a separate account for each symbol along with an account for the cash on hand, the commissions paid,
        and an overall total for the portfolio value.
        '''
        d = dict( (k, v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def construct_current_holdings(self):
        '''
        Constructs the holdings dictionary that is "as of now"
        '''

        # why is it not taking in values based on trades?
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d

    def update_timeindex(self, event):
        '''
        Adds a new record to the positions matrix for the current market data bar.
        This reflects the PREVIOUS bar, i.e. all current market data at this stage is known (OHLCV)

        Makes use of a MarketEvent from the events queue.
        '''
        latest_datetime = self.bars.get_latest_bar_datetime( self.symbol_list[0] )

        # Update positions
        # ================
        dp = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        dp['datetime'] = latest_datetime

        for s in self.symbol_list:
            dp[s] = self.current_positions[s]

        # Append the current positions
        self.all_positions.append(dp)

        # Update holdings
        # ===============
        dh = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']

        for s in self.symbol_list:
            # Approximation of the real value
            market_value = self.current_positions[s] * self.bars.get_latest_bar_value(s, 'Adj_Close')
            dh[s] = market_value
            dh['total'] += market_value

        # Append the holdings
        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill):
        '''
        Takes in a Fill object (event?) and updates the position matrix (dict?) accordingly to reflect the new position

        Parameters:
        fill - The Fill object (event?) to update the positions with
        '''
        # check whether the fill is a buy or sell
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1

        # update positions list with new quantities
        self.current_positions[fill.symbol] += fill_dir * fill.quantity

    def update_holdings_from_fill(self, fill):
        '''
        Tales in a Fill object (event?) and updates the holings matrix (dict?) accordingly to reflect the holdings value

        Parameters:
        fill - The Fill object (event?) to update the holdings with
        '''
        # check whether the fill is a buy or sell
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1

        # Update holdings list with new quantities
        fill_cost = self.bars.get_latest_bar_value(fill.symbol, 'Adj_Close')
        cost = fill_dir * fill_cost * fill.quantity
        self.current_holdings[fill.symbol] += cost # update the holdings for the symbol we traded
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= (cost + fill.commission) # WARNING : is this right???

    def update_fill(self, event):
        '''
        Updates the portfolio current positions and holdings from the FillEvent

        Serves as a wrapper around update_positions_from_fill() and update_holdings_from_fill()
        '''
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def generate_naive_order(self, signal):
        '''
        Generates an Order object (event?) with a constant quantity of shares to purchase

        Parameters:
        signal - A tuple containing the Signal information
        '''
        order = None

        symbol = signal.symbol
        direction = signal.signal_type
        strength = signal.strength

        mkt_quantity = 100
        cur_quantity = self.current_positions[symbol]
        order_type = 'MKT'

        # only buy if current hold 0 shares of the symbol
        if direction == 'LONG' and cur_quantity == 0: # long stock
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
        if direction == 'SHORT' and cur_quantity == 0: # short stock
            order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')

        if direction == 'EXIT' and cur_quantity > 0: # sell to close
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
        if direction == 'EXIT' and cur_quantity < 0: # buy to cover
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY')

        return order

    def generate_percentage_order(self, signal):
        '''
        Generates an OrderEvent with a constant percentage of shares to purchase

        Parameters:
        signal - A tuple containing the Signal information
        '''
        order = None

        symbol = signal.symbol
        direction = signal.signal_type
        strength = signal.strength

        current_price = self.bars.get_latest_bar_value(signal.symbol, 'Adj_Close')
        current_date = self.bars.get_latest_bar_datetime(signal.symbol).date()
        mkt_quantity = floor((self.initial_capital * 0.05) / current_price) #100
        cur_quantity = self.current_positions[symbol]
        order_type = 'MKT'

        # only buy if current hold 0 shares of the symbol
        if direction == 'LONG' and cur_quantity == 0: # long stock
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
            print(str(current_date) + ': Buying ' + str(mkt_quantity) + ' of ' + symbol + ' at ' + str(current_price))
            print('\n')
        if direction == 'SHORT' and cur_quantity == 0: # short stock
            order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')
            print(str(current_date) + ': Shorting ' + str(mkt_quantity) + ' of ' + symbol + ' at ' + str(current_price))
            print('\n')

        if direction == 'EXIT' and cur_quantity > 0: # sell to close
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
            print(str(current_date) + ': Selling to close ' + str(abs(cur_quantity)) + ' of ' + symbol + ' at ' + str(current_price))
            print('\n')
        if direction == 'EXIT' and cur_quantity < 0: # buy to cover
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY')
            print(str(current_date) + ': Buying to cover ' + str(abs(cur_quantity)) + ' of ' + symbol + ' at ' + str(current_price))
            print('\n')

        return order

    def update_signal(self, event):
        '''
        Acts when a SignalEvent is generated to create new orders based on the portfolio logic
        '''
        if event.type == 'SIGNAL':
            # order_event = self.generate_naive_order(event)
            order_event = self.generate_percentage_order(event)
            self.events.put(order_event)

    def create_equity_curve_dataframe(self):
        '''
        Creates a pandas DataFrame from the all_holdings list of dictionaries
        '''
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace = True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
        self.equity_curve = curve

    def output_summary_stats(self, strategy_title):
        '''
        Creates a list of summary statistics for the portfolio.
        '''
        total_return = self.equity_curve['equity_curve'][-1]
        returns = self.equity_curve['returns']
        pnl = self.equity_curve['equity_curve']

        sharpe_ratio = create_sharpe_ratio(returns, periods = 252) # i guess this is for minute resolution
        drawdown, max_dd, dd_duration = create_drawdowns(pnl)
        self.equity_curve['drawdown'] = drawdown

        stats = ['Total Return', '%0.2f%%' % ((total_return - 1.0) * 100.0),
                 ('Sharpe Ratio', '%0.2f' % sharpe_ratio),
                 ('Max Drawdown', '%0.2f%%' % (max_dd * 100.0)),
                 ('Drawdown Duration', '%d' % dd_duration)]
        self.equity_curve.to_csv('equity.csv')
        self.print_chart(max_dd, dd_duration, total_return, sharpe_ratio, strategy_title)
        return stats

    def print_chart(self, max_dd, dd_duration, total_return, sharpe_ratio, strategy_title):
        '''
        Outputs a chart to the screen to show the summary stats
        '''
        strategy_return = np.round((total_return - 1.0) * 100.0, 2)
        strategy_drawdown = np.round(max_dd * 100.0, 2)

        drawdowns = self.equity_curve['drawdown'] * 100
        returns = self.equity_curve['equity_curve']
        base = [1.00] * len(returns)

        fig, axes = plt.subplots(2, 1, figsize = (15, 10))
        fig.suptitle(strategy_title, fontsize = 20)

        returns.plot(ax = axes[0], title = 'Equity Curve: Total Return = ' + str(strategy_return) + '%, Sharpe Ratio = ' + str(np.round(sharpe_ratio, 1)),
                                                color = 'black', linewidth = 1.5)
        axes[0].fill_between(returns.index, returns, base, where = returns >= base, color = 'limegreen', alpha = 0.3 )
        axes[0].fill_between(returns.index, returns, base, where = returns < base, color = 'red', alpha = 0.3 )
        axes[0].grid(linestyle = '--')
        axes[0].set_xlabel('')

        drawdowns.plot(ax = axes[1], title = 'Drawdowns: Max Drawdown = ' + str(strategy_drawdown) + '%, Max Drawdown Duration = ' + str(dd_duration) + ' days',
                                            color = 'black', linewidth = 1.5)
        axes[1].fill_between(drawdowns.index, 0, drawdowns.values, facecolor = 'orange', alpha = 0.5)
        axes[1].yaxis.set_major_formatter(PercentFormatter())
        axes[1].grid(linestyle = '--')
        axes[1].set_ylim([(strategy_drawdown*2), 0])
        axes[1].set_xlabel('')

        for ax in axes:
            ax.title.set_fontsize(15)

        plt.tight_layout(rect=[0, 0.01, 1, 0.92])
        plt.show()
