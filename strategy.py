# strategy.py

from __future__ import print_function

from abc import ABCMeta, abstractmethod
import datetime
try:
    import Queue as queue
except ImportError:
    import queue

import numpy as np
import pandas as pd

from event import SignalEvent

class Strategy(object):
    '''
    An abstract base class used to provide an abstracted interface for all subclasses used to handle the strategies

    The goal of a Strategy subclass is to generate Signal objects for specific symbols based on the inputs of
    bars (and maybe other stuff) generated by a DataHandler object.

    This is designed to work with historic and live data because the Strategy object is agnostic to where the data comes from
    as it obtains the bar tuples from a queue object which is derived elsewhere in the program
    '''

    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate_signals(self):
        '''
        Provides the mechanisms to calculate the list of signals
        '''
        raise NotImplementedError('Should implement calculate_signals()')