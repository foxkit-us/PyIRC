# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


try:
    from enum import Enum
except ImportError:
    from PyIRC.util.enum import Enum

from types import SimpleNamespace
from collections import namedtuple
from logging import getLogger


logger = getLogger(__name__)


class EventState(Enum):
    """ The current state of an event. """

    ok = 0
    """ Proceed with other callbacks, if any. """
    cancel = 1
    """ Event is cancelled; do not run any further callbacks. """
    terminate_soon = 2
    """ Send a QUIT to the IRC server. """
    terminate_now = 3
    """ Abort the entire library immediately.

    .. warning:: This state should only be used if data loss may occur.
    """


class Event:
    """ Basic event passing through """

    def __init__(self, event):
        self.event = event
        self.status = EventState.ok
        self.cancel_function = None


class HookEvent(Event):
    """ A hook has been called """

    pass


class LineEvent(Event):
    """ A line event """

    def __init__(self, event, line):
        super().__init__(event)

        self.line = line


EventRegistry = namedtuple("EventRegistry", "events type")


class EventManager:
    """EventManager manages event registration and dispatch.

    The following attributes are available:

    events_reg
        The hclass to (events, type) mapping. Useful for advanced usage.
    """

    def __init__(self):
        # Contains event classes
        self.events_reg = dict()

    def register_class(self, hclass, type):
        """ Register a class of events.

        hclass
            The name of the event class.
        type
            The type of :py:class:`Event` that will be passed to event handlers.

        If ``hclass`` is already a registered event class, this method is a no-op.
        To change the type of :py:class:`Event` that will be passed to handlers,
        you must unregister the class using :py:meth:`unregister_class` and
        re-register it with the new type.
        """

        if hclass in self.events_reg:
            return

        logger.debug("Registering class %s with type %s", hclass, type.__name__)

        # Set the events list
        self.events_reg[hclass] = EventRegistry(dict(), type)

    def unregister_class(self, hclass):
        """ Unregister a class of events. """

        assert hclass in self.events_reg

        logger.debug("Unregistering class %s", hclass)

        del self.events_reg[hclass]

    def clear(self):
        """ Unregister all event classes.

        .. warning::
            This will clear all callbacks, events, and event classes.
            Do not use unless you really know what you're doing.
        """

        logger.debug("Clearing hooks")
        self.events_reg.clear()

    def register_event(self, hclass, event):
        """ Register an event to a given class.

        hclass
            The class of the event to register.
        event
            The name of the event to register.

        If ``event`` is already registered in ``hclass``, this method is a no-op.
        """

        assert hclass in self.events_reg

        events = self.events_reg[hclass][0]

        if event in events:
            return

        events[event] = SimpleNamespace()
        events[event].items = []
        events[event].cur_id = 0

    def unregister_event(self, hclass, event):
        """ Unregister an event from a given class.

        hclass
            The class of the event to unregister.
        event
            The name of the event to unregister.

        .. note:: It is an error to unregister an event that does not exist.
        """

        assert hclass in self.events_reg

        events = self.events_reg[hclass][0]

        if event not in events:
            return

        del events[event]

    def register_callback(self, hclass, event, priority, callback):
        """ Register a callback for an event.

        You typically should never call this method directly; instead, use the
        @hook decorator.

        hclass
            The class of the event to register with this callback.
        event
            The name of the event to register with this callback.
        priority
            The priority of this callback with this event.
        callback
            A Callable to invoke when this event occurs.
        """

        # Does nothing if not needed
        self.register_event(hclass, event)

        events = self.events_reg[hclass][0]

        # Increment unique event ID
        cur_id = events[event].cur_id
        events[event].cur_id += 1

        item = [priority, cur_id, callback]
        events[event].items.append(item)
        events[event].items.sort()

    def register_callbacks_from_inst(self, hclass, inst, key=None):
        """ Register callbacks from a given instance, using hook tables

        hclass
            The class of the event to register with this callback
        inst
            The class to process
        key
            function to use to transform keys in the table
        """
        attr = hclass + '_hooks'
        table = getattr(inst, attr, None)
        if table is None:
            return False

        self.register_callbacks_from_table(hclass, table, key)

    def register_callbacks_from_table(self, hclass, table, key=None):
        """ Register callbacks from the given hook table.

        hclass
            The class of the event to register with this callback
        table
            The table to process
        key
            function to use to transform keys in the table
        """
        for hook, (callback, priority) in table.items():
            if key:
                hook = key(hook)

            self.register_callback(hclass, hook, priority, callback)

    def unregister_callback(self, hclass, event, callback):
        """ Unregister a callback for an event.

        hclass
            The class of the event to unregister this callback from.
        event
            The name of the event to unregister this callback from.
        callback
            The callback to unregister.
        """

        assert hclass in self.events_reg

        events = self.events_reg[hclass][0]
        assert event in events

        items = events[event].items

        # Build the deletion list (can't delete whilst iterating)
        remove = []
        for i, (_, _, l_callback) in enumerate(items):
            if l_callback is callback:
                remove.append(i)

        if not remove:
            raise ValueError("Event not found")

        for i in remove:
            del items[i]

    def call_event(self, hclass, event, *args):
        """ Call the callbacks for a given event.

        hclass
            The class of the event that is occuring.
        event
            The name of the event that is occuring.
        ``*args``
            The arguments to pass to the :py:class:`Event` type constructor used
            for the event class.
        """

        assert hclass in self.events_reg

        events, type = self.events_reg[hclass]
        if event not in events:
            return None

        items = events[event].items
        if not items:
            return None

        ev_inst = type(event, *args)

        for _, _, function in items:
            ret = function(ev_inst)
            if ev_inst.status == EventState.ok:
                continue
            elif ev_inst.status == EventState.cancel:
                EventState.cancel_function = function
                break
            elif ev_inst.status == EventState.terminate_now:
                quit()

        return ev_inst
