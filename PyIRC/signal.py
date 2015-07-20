# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Decorator and helpers connecting the PyIRC event system to Taillight."""


from collections import defaultdict
from inspect import getmembers
from logging import getLogger

from taillight.signal import UnsharedSignal
from taillight import ANY

try:
    from enum import Enum
except ImportError:
    from PyIRC.util.enum import Enum


_logger = getLogger(__name__)  # pylint: disable=invalid-name


def event(hclass, event_name, priority=UnsharedSignal.PRIORITY_NORMAL,
          listener=ANY):
    """Tag a function as an event for later binding.

    This function is a decorator.

    :param hclass:
        Name of the event class.

    :param event_name:
        Name of the event.

    :param priority:
        Priority of the signal

    :param listener:
        Listener of the signal.

    """

    if isinstance(event_name, Enum):
        # FIXME - workaround!
        event_name = event_name.value

    name = (hclass, event_name)

    def wrapped(function):
        if not hasattr(function, '_signal'):
            function._signal = list()

        function._signal.append((name, priority, listener))

        return function

    return wrapped


class SignalDict(dict):
    """A dictionary used for unshared Taillight signals."""
    def __missing__(self, key):
        value = self[key] = UnsharedSignal(key)
        return value


class SignalStorage:
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
        self.signals = SignalDict()
        self.signal_slots = defaultdict(list)

    def bind(self, inst):
        """Bind slots from `inst` to their respective signals."""
        slots = self.signal_slots[id(inst)]
        for (_, function) in getmembers(inst, self._signal_pred):
            for param in function._signal:
                signal = self.get_signal(param[0])
                slots.append(signal.add(function, *param[1:]))

    def unbind(self, inst):
        """Remove slots from `inst` from their respective signals."""
        for slot in self.signal_slots[id(inst)]:
            slot.signal.delete(slot)

    def get_signal(self, name):
        """Retrieve the specified signal for this PyIRC instance."""
        return self.signals[name]

    def __contains__(self, name):
        return name in self.signals
