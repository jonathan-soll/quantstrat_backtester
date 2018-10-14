# execution.py

from __future__ import print_function
from abc import ABCMeta, abstractmethod
import datetime
try:
    import Queue as queue
except ImportError:
    import queue

from event import FillEvent, OrderEvent

class ExecutionHandler(object):
    '''
    The ExecutionHandler abstract class handles the interaction between a set of order objects (events?) generated
    by a Portfolio and the ultimate set of Fill objects (event?) that actually occur in the market.

    The handlers can be used to subclass simulated brokerages or live brokerages, with identical interfaces. This
    will allow us to backtest strategies in a very similar manner to the live trading engine.
    '''

    __metaclass__ = ABCMeta

    @abstractmethod
    def execute_order(self, event):
        '''
        Takes an Order event and executes it, producing a Fill event that gets placed in the Events queue

        Parameters:
        event - Contains an Event object with order information
        '''
        raise NotImplementedError("Should implement execute_order()")

class SimulatedExecutionHandler(ExecutionHandler):
    '''
    This ExecutionHandler class is the simplest of execution handlers because it will simply assume all orders
    are filled automatically with no latency, slippage or fill-ratio issues.
    '''

    def __init__(self, events):
        '''
        Initializes the ExecutionHandler, settng the event queues up internalls

        Parameters:
        events - The Queue of Event objects
        '''
        self.events = events

    def execute_order(self, event):
        '''
        Converts Order Events into Fill Events automatically with no latency, slippage or other real-world considerations

        Parameters:
        event  - contains an Event object with order information
        '''

        '''
        FillEvent initialization parameters below for convenience

        timeindex, symbol, exchange, quantity, direction, fill_cost, commission=None)
        '''
        if event.type == 'ORDER':
            fill_event = FillEvent(
                timeindex = datetime.datetime.utcnow(),
                symbol = event.symbol,
                exchange = 'ARCA',
                quantity = event.quantity,
                direction = event.direction,
                fill_cost = None # no fill_cost because we modeled the cost of ill in the Portfolio object
            )
            self.events.put(fill_event)
