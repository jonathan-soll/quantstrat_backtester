# event.py

from __future__ import print_function

class Event(object):
    '''
    Event is the blase class for providing an interface for all subsequent (inherited events),
    which will trigger further events in the trading program
    '''

    pass


class MarketEvent(Event):
    '''
    Handles the event of receiving a new market update with corresponding bars
    '''

    def __init__(self):
        '''
        Initialises the MarketEvent
        '''
        self.type = 'MARKET'


class SignalEvent(Event):
    '''
    Handles the event of sending a Signal from a Strategy object. This is received by a Portfolio object and acted upon.
    '''

    def __init__(self, strategy_id, symbol, datetime, signal_type, strength):
        '''
        Initializes the SignalEvent

        Parameters:
        strategy_id - the unique identifier for the strategy that generated the SignalEvent
        symbol - the ticker symbol (e.g. 'AAPL')
        datetime - the timestamp at which the signal was generated
        signal_type - 'LONG' or 'SHORT' (or EXIT?)
        strength - An adjustment factor 'suggestion' used to scale quantity of trade.
        '''

        self.type = 'SIGNAL'
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength


class OrderEvent(Event):
    '''
    Handles the event of sending an Order to an execution system.
    The order contains a symbol (e.g. 'AAPL'), a type (market or limit), a quantity and a direction
    '''

    def __init__(self, symbol, order_type, quantity, direction):
        '''
        Initializes the order type, setting whether it is a Market order ('MKT') or Limit ('LMT')
        it has a quantity and its direction ('BUY' or 'SELL')

        Parameters:
        symbol - the instrument to trade
        order_type - 'MKT' or 'LMT'
        quantity - number instruments to trade
        direction - 'BUY' or 'SELL'
        '''

        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction

    def print_order(self):
        '''
        Outputs the values within the Order
        '''
        print(
            'Order: Symbol = %s, Type = %s, Quantity = %s, Direction = %s' % (self.symbol, self.order_type
                                                                              , self.quantity, self.direction)
        )


# event.py

class FillEvent(Event):
    '''
    Represents a filled order from a brokerage. It stores the quantity of an instrument bought or solf and at what price.
    Additionally stores the commission of the trade.
    '''

    def __init__(self, timeindex, symbol, exchange, quantity,
                direction, fill_cost, commission=None):
        '''
        Initializes the FillEvent object. Sets the symbol, exchange, quantity, direction, cost, and commission

        For commission, the object defaults to IB fees.

        Parameters:
        timeindex - the bar-resolution when the order was filled
        symbol - the instrument that was traded
        exchange - the exchange where the order was filled
        quantity - the filled quantity
        direction - 'BUY' or 'SELL'
        fill_cost - the value of the holdings in dollars
        commission - commission charged by brokerage
        '''

        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost

        # calculate the commissions
        if commission is None:
            self.commission = self.calculate_ib_commission()
        else:
            self.commission = commission

    def calculate_ib_commission(self):
        '''
        Calculate the fees based on what IB charges.
        $1.30 minimum, 0.013 USD or 0.008 USD per share depending on if trade size is above or below 500 shares

        Does not include exchange or ECN fees.
        '''
        full_cost = 1.3
        if self.quantity <= 500:
            full_cost = max(1.3, 0.013 * self.quantity)
        else:
            full_cost = max(1.3, 0.008 * self.quantity)

        return full_cost
