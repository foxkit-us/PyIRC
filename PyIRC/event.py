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
    """ EventManager manages event registration and dispatch. """

    def __init__(self):
        # Contains event classes
        self.events_reg = dict()

    def register_class(self, cls, type):
        """ Register a class of events.

        cls
            The name of the event class.
        type
            The type of :py:class:`Event` that will be passed to event handlers.

        If ``cls`` is already a registered event class, this method is a no-op.
        To change the type of :py:class:`Event` that will be passed to handlers,
        you must unregister the class using :py:meth:`unregister_class` and
        re-register it with the new type.
        """

        if cls in self.events_reg:
            return

        logger.debug("Registering class %s with type %s", cls, type.__name__)

        # Set the events list
        self.events_reg[cls] = EventRegistry(dict(), type)

    def unregister_class(self, cls):
        """ Unregister a class of events. """

        assert cls in self.events_reg

        logger.debug("Unregistering class %s", cls)

        del self.events_reg[cls]

    def clear(self):
        """ Unregister all event classes.

        .. warning::
            This will clear all callbacks, events, and event classes.
            Do not use unless you really know what you're doing.
        """

        logger.debug("Clearing hooks")
        self.events_reg.clear()

    def register_event(self, cls, event):
        """ Register an event to a given class.

        cls
            The class of the event to register.
        event
            The name of the event to register.

        If ``event`` is already registered in ``cls``, this method is a no-op.
        """

        assert cls in self.events_reg

        events = self.events_reg[cls][0]

        if event in events:
            return

        events[event] = SimpleNamespace()
        events[event].items = []
        events[event].cur_id = 0

    def unregister_event(self, cls, event):
        """ Unregister an event from a given class.

        cls
            The class of the event to unregister.
        event
            The name of the event to unregister.

        .. note:: It is an error to unregister an event that does not exist.
        """

        assert cls in self.events_reg

        events = self.events_reg[cls][0]

        if event not in events:
            return

        del events[event]

    def register_callback(self, cls, event, priority, callback):
        """ Register a callback for an event.

        You typically should never call this method directly; instead, use the
        @hook decorator.

        cls
            The class of the event to register with this callback.
        event
            The name of the event to register with this callback.
        priority
            The priority of this callback with this event.
        callback
            A Callable to invoke when this event occurs.
        """

        # Does nothing if not needed
        self.register_event(cls, event)

        events = self.events_reg[cls][0]

        # Increment unique event ID
        cur_id = events[event].cur_id
        events[event].cur_id += 1

        item = [priority, cur_id, callback]
        events[event].items.append(item)
        events[event].items.sort()

    def unregister_callback(self, cls, event, callback):
        """ Unregister a callback for an event.

        cls
            The class of the event to unregister this callback from.
        event
            The name of the event to unregister this callback from.
        callback
            The callback to unregister.
        """

        assert cls in self.events_reg

        events = self.events_reg[cls][0]
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

    def call_event(self, cls, event, *args):
        """ Call the callbacks for a given event.

        cls
            The class of the event that is occuring.
        event
            The name of the event that is occuring.
        ``*args``
            The arguments to pass to the :py:class:`Event` type constructor used
            for the event class.
        """

        assert cls in self.events_reg

        events, type = self.events_reg[cls]
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
