# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from collections import defaultdict
from inspect import getmembers

from taillight.signal import Signal
from taillight import ANY

try:
    from enum import Enum
except ImportError:
    from PyIRC.util.enum import Enum


def event(hclass, event, priority=Signal.PRIORITY_NORMAL, listener=ANY):
    """Tag a function as an event for later binding.

    This function is a decorator.

    :param hclass:
        Name of the event class.

    :param event:
        Name of the event.

    :param priority:
        Priority of the signal

    :param listener:
        Listener of the signal.

    """

    if isinstance(event, Enum):
        # FIXME - workaround!
        event = event.value

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

    def __init__(self):
        if not hasattr(self, "signals"):
            # This could be redirecting to another class
            self.signals = defaultdict(Signal)

        self.signal_slots = []
        for (name, function) in getmembers(self, self._signal_pred):
            for param in function._signal:
                signal_name = param[0]
                signal = self.signals[signal_name]
                self.signal_slots.append(signal.add(function, *param[1:]))

    def __contains__(self, name):
        return name in self.signals

