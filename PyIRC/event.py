# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""The event subsystem

PyIRC is built on a powerful yet easy-to-use event system.  In addition to
command events (each command and numeric has its own event you can hook), your
code can define its own event types wherever necessary - for example, the CTCP
extension defines a CTCP message event.
"""


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

    @staticmethod
    def key(k):
        """Key function"""
        return k.lower()


class HookEvent(Event):
    """ A hook has been called """

    pass


class LineEvent(Event):
    """ A line event """

    def __init__(self, event, line):
        super().__init__(event)

        self.line = line

    @staticmethod
    def key(k):
        return k.lower() if isinstance(k, str) else k.value


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

        events = self.events_reg[hclass].events

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

        events = self.events_reg[hclass].events

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

        events = self.events_reg[hclass].events
        keyfunc = self.events_reg[hclass].type.key
        event = keyfunc(event)

        # Does nothing if not needed
        self.register_event(hclass, event)

        # Increment unique event ID
        cur_id = events[event].cur_id
        events[event].cur_id += 1

        item = [priority, cur_id, callback]
        events[event].items.append(item)
        events[event].items.sort()

    def register_callbacks_from_inst_all(self, inst):
        """ Register all (known) callback classes from a given instance, using
        hook tables

        Arguments:

        inst
            The instance to process
        """
        for hclass in self.events_reg.keys():
            self.register_callbacks_from_inst(hclass, inst)

    def register_callbacks_from_inst(self, hclass, inst):
        """ Register callbacks from a given instance, using hook tables

        Arguments:

        hclass
            The instance of the event to register with this callback
        inst
            The instance to process
        """
        attr = hclass + '_hooks'
        table = getattr(inst, attr, None)
        if table is None:
            return False

        logger.debug("Registering %s callbacks from class %s:",
                     hclass, inst.__class__.__name__)

        self.register_callbacks_from_table(hclass, table)
        return True

    def register_callbacks_from_table(self, hclass, table):
        """ Register callbacks from the given hook table.

        hclass
            The class of the event to register with this callback
        table
            The table to process
        """
        for event, (callback, priority) in table.items():
            self.register_callback(hclass, event, priority, callback)

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

        events = self.events_reg[hclass].events
        keyfunc = self.events_reg[hclass].type.key
        event = keyfunc(event)
        assert event in events
        items = events[event].items

        remove = False
        for i, (_, _, l_callback) in enumerate(list(items)):
            if l_callback is callback:
                del items[i]
                remove = True

        if not remove:
            raise ValueError("Event not found")

        logger.debug("Unregistering callback for hclass %s event %s: %r",
                     hclass, event, callback)

    def unregister_callbacks_from_inst_all(self, inst):
        """ Unregister all (known) callback classes from a given instance, using
        hook tables

        Arguments:

        inst
            The instance to process
        """
        for hclass in self.events_reg.keys():
            self.unregister_callbacks_from_inst(hclass, inst)

    def unregister_callbacks_from_inst(self, hclass, inst):
        """ Unregister callbacks from a given instance, using hook tables

        Arguments:

        hclass
            The class of the event to register with this callback
        inst
            The class to process
        """
        attr = hclass + '_hooks'
        table = getattr(inst, attr, None)
        if table is None:
            return False

        logger.debug("Unregistering %s callbacks from class %s:",
                     hclass, inst.__class__.__name__)

        self.unregister_callbacks_from_table(hclass, table)
        return True

    def unregister_callbacks_from_table(self, hclass, table):
        """ Unregister callbacks from the given hook table.

        Arguments:

        hclass
            The class of the event to register with this callback
        table
            The table to process
        """
        for event, (callback, _) in table.items():
            self.unregister_callback(hclass, event, callback)

    def call_event(self, hclass, event, *args):
        """ Call the callbacks for a given event.

        Arguments:

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
        keyfunc = type.key
        event = keyfunc(event)
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
