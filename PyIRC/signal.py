# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from collections import defaultdict

from taillight.signal import Signal
from taillight import ANY


class SignalBase:
    """A helper class for scanning signals.
    
    Since bound methods belong to the class instances and not the class itself,
    and signals would overlap if we simply added each bound method as a signal,
    we use this as a helper class.

    The idea is Signals are bound to dictionary values, stored in this class.
    This will use an existing dictionary if present; otherwise, it will simply
    create a new one.

    """

    signal_wrapped = defaultdict(list)
    "A list of event-wrapped functions"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not hasattr(self, "signals"):
            # This could be redirecting to another class
            self.signals = defaultdict(Signal)

        self.signal_slots = []
        for function, param in self.signal_wrapped.items():
            signal = self.signals[name]
            self.signal_slots.append(signal.add(*param))

    def __contains__(self, name):
        return name in self.signals

    @classmethod
    def signal_event(cls, name, priority=Signal.PRIORITY_NORMAL,
                     listener=ANY):
        """The decorator to use for class members and signals."""

        def wrapped(function):
            l = cls.signal_wrapped[function]
            l.append((name, priority, listener))
            
            return function

        return wrapped
