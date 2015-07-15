# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from collections import defaultdict
from inspect import getmembers

from taillight.signal import Signal
from taillight import ANY


def event(hclass, event, priority=Signal.PRIORITY_NORMAL, listener=ANY):
    """Tag a function as an event for later binding.

    This function is a decorator.

    :param name:
        Name of the signal.

    :param priority:
        Priority of the signal

    :param listener:
        Listener of the signal.

    """
    name = (hclass, event)
    def wrapped(function):
        if not hasattr(function, '_signal'):
            function._signal = list()

        function._signal.append((name, priority, listener))

        return function

    return wrapped


class SignalBase:
    """A helper class for scanning signals.
    
    Since bound methods belong to the class instances and not the class itself,
    and signals would overlap if we simply added each bound method as a signal,
    we use this as a helper class.

    The idea is Signals are bound to dictionary values, stored in this class.
    This will use an existing dictionary if present; otherwise, it will simply
    create a new one.

    """

    @staticmethod
    def _signal_pred(member):
        return hasattr(member, "_signal")

    def __init__(self, *args, **kwargs):
        #super().__init__(*args, **kwargs)

        if not hasattr(self, "_signals"):
            # This could be redirecting to another class
            self._signals = dict()

        self.signal_slots = []
        for (name, function) in getmembers(self, self._signal_pred):
            param = function._signal
            signal = self._signals.get(param[0], Signal(param[0]))
            self.signal_slots.append(signal.add(function, *param))
            print("signal: {}".format(repr(signal)))

    def __contains__(self, name):
        return name in self.signals

