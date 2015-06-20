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

    """The current state of an event."""

    ok = 0
    """Proceed with other callbacks, if any. """

    cancel = 1
    """Event is cancelled; do not run any further callbacks. """

    terminate_soon = 2
    """Send a QUIT to the IRC server. """

    terminate_now = 3
    """Abort the entire library immediately.

    .. warning:: This state should only be used if data loss may occur.
    """

    pause = 4
    """Pause the callback chain for later resumption """


class Event:

    """The base class for all events passed to callbacks.

    :ivar status:
        The current status of the event.

    :ivar last_function:
        Set to the function who cancelled us, if we are cancelled.
    """

    __slots__ = ('event', 'status', 'last_function', 'pause_state')

    def __init__(self, event):
        """Initalise the event object

        Arguments:

        :param event:
            The event type occuring
        """
        self.event = event
        self.status = EventState.ok
        self.last_function = None

        # Used for pausing events
        self.pause_state = None

    @staticmethod
    def key(k):
        """Key function"""
        return k.lower()


class HookEvent(Event):

    """The event for hooks"""


class LineEvent(Event):

    """The event for lines"""

    def __init__(self, event, line):
        """Initalise a LineEvent object.

        :param event:
            The event type occurring, should mirror line.command.
        :param line:
            The parsed IRC message of this event
        """
        super().__init__(event)

        self.line = line

    @staticmethod
    def key(k):
        return k.lower() if isinstance(k, str) else k.value


EventRegistry = namedtuple("EventRegistry", "events type")


class EventManager:

    """EventManager manages event registration and dispatch.

    :ivar events_reg:
        The hclass to (events, type) mapping. Useful for advanced usage.
    """

    def __init__(self):
        # Contains event classes
        self.events_reg = dict()

    def register_class(self, hclass, type):
        """Register a class of events.

        :param hclass:
            The name of the event class. If this name is already registered,
            this method is a no-op. To change the
            py:class:`~PyIRC.event.Event` type for a given class, you must
            unregister the class with
            :py:meth:`~PyIRC.event.EventManager.unregister_class`, and then
            re-register it wiht the new type.

        :param type:
            The type of :py:class:`~PyIRC.event.Event` that will be passed to
            event handlers.
        """

        if hclass in self.events_reg:
            return

        logger.debug("Registering class %s with type %s", hclass, type.__name__)

        # Set the events list
        self.events_reg[hclass] = EventRegistry(dict(), type)

    def unregister_class(self, hclass):
        """Unregister a class of events. """
        if hclass not in self.events_reg:
            raise KeyError("hclass not found")

        logger.debug("Unregistering class %s", hclass)

        del self.events_reg[hclass]

    def clear(self):
        """Unregister all event classes.

        .. warning::
            This will clear all callbacks, events, and event classes.
            Do not use unless you really know what you're doing.
        """
        logger.debug("Clearing hooks")
        self.events_reg.clear()

    def register_event(self, hclass, event):
        """Register an event to a given class.

        :param hclass:
            The class of the event to register.

        :param event:
            The name of the event to register.

        If ``event`` is already registered in ``hclass``, this method is a no-op.
        """
        if hclass not in self.events_reg:
            raise KeyError("hclass not found")

        events = self.events_reg[hclass].events

        if event in events:
            return

        events[event] = SimpleNamespace()
        events[event].items = []
        events[event].cur_id = 0

    def unregister_event(self, hclass, event):
        """Unregister an event from a given class.

        :param hclass:
            The class of the event to unregister.

        :param event:
            The name of the event to unregister.

        .. note:: It is an error to unregister an event that does not exist.
        """
        if hclass not in self.events_reg:
            raise KeyError("hclass not found")

        events = self.events_reg[hclass].events

        if event not in events:
            return

        del events[event]

    def register_callback(self, hclass, event, priority, callback):
        """Register a callback for an event.

        This method should only be used directly if you know what you're
        doing.

        :param hclass:
            The class of the event to register with this callback.

        :param event:
            The name of the event to register with this callback.

        :param priority:
            The priority of this callback with this event.

        :param callback:
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
        """Register all (known) callback classes from a given instance, using
        hook tables

        :param inst:
            The instance to process
        """
        for hclass in self.events_reg.keys():
            self.register_callbacks_from_inst(hclass, inst)

    def register_callbacks_from_inst(self, hclass, inst):
        """Register callbacks from a given instance, using hook tables

        :param hclass:
            The instance of the event to register with this callback

        :param inst:
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
        """Register callbacks from the given hook table.

        :param hclass:
            The class of the event to register with this callback.

        :param table:
            The table to process.
        """
        for event, (callback, priority) in table.items():
            self.register_callback(hclass, event, priority, callback)

    def unregister_callback(self, hclass, event, callback):
        """Unregister a callback for an event.

        :param hclass:
            The class of the event to unregister this callback from.

        :param event:
            The name of the event to unregister this callback from.

        :param callback:
            The callback to unregister.
        """
        if hclass not in self.events_reg:
            raise KeyError("hclass not found")

        events = self.events_reg[hclass].events
        keyfunc = self.events_reg[hclass].type.key
        event = keyfunc(event)
        assert event in events
        items = events[event].items

        remove = False
        for i, (_, _, l_callback) in enumerate(list(items)):
            if l_callback == callback:
                del items[i]
                remove = True

        if not remove:
            raise ValueError("Event not found")

        logger.debug("Unregistering callback for hclass %s event %s: %r",
                     hclass, event, callback)

    def unregister_callbacks_from_inst_all(self, inst):
        """Unregister all (known) callback classes from a given instance, using
        hook tables

        :param inst:
            The instance to process
        """
        for hclass in self.events_reg.keys():
            self.unregister_callbacks_from_inst(hclass, inst)

    def unregister_callbacks_from_inst(self, hclass, inst):
        """Unregister callbacks from a given instance, using hook tables.

        :param hclass:
            The class of the event to register with this callback.

        :param inst:
            The class to process.
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
        """Unregister callbacks from the given hook table.

        :param hclass:
            The class of the event to register with this callback.

        :param table:
            The table to process
        """
        for event, (callback, _) in table.items():
            self.unregister_callback(hclass, event, callback)

    def call_event(self, hclass, event, *args, **kwargs):
        """Call the callbacks for a given event.

        :param hclass:
            The class of the event that is occuring.

        :param event:
            The name of the event that is occuring.

        :param \*args:
            The arguments to pass to the :py:class:`~PyIRC.event.Event` type constructor used
            for the event class.
        """
        if hclass not in self.events_reg:
            raise KeyError("hclass not found")

        type = self.events_reg[hclass].type
        event = type.key(event)
        return self.call_event_inst(hclass, event,
                                    type(event, *args, **kwargs))

    def _call_generator(self, events, event_inst):
        for _, _, function in events:
            event_inst.last_function = function
            function(event_inst)
            yield event_inst.status

    def call_event_inst(self, hclass, event, event_inst):
        """Call an event with the given event instance.

        If the event is paused, it will resume calling unless cancelled.

        :param hclass:
            The class of the event that is occuring.

        :param event:
            The name of the event that is occuring.

        :param event_inst:
            The :py:class:`~PyIRC.event.Event` type we are reusing for this call.
        """
        if hclass not in self.events_reg:
            raise KeyError("hclass not found")

        events, type = self.events_reg[hclass]
        keyfunc = type.key
        event = keyfunc(event)
        if event not in events:
            return

        if event_inst.pause_state:
            gen = event_inst.pause_state
            event_inst.pause_state = None
            logger.debug("Resuming event: %r", gen)
        else:
            items = events[event].items
            if not items:
                return

            gen = self._call_generator(items, event_inst)

        for status in gen:
            if status == EventState.ok:
                continue
            elif status == EventState.pause:
                logger.debug("Pausing event: %r", gen)
                event_inst.pause_state = gen
                break
            elif status == EventState.cancel:
                break
            elif status == EventState.terminate_now:
                quit()

        return event_inst
