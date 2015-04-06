# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


from enum import Enum
from types import SimpleNamespace
from collections import namedtuple
from logging import getLogger


logger = getLogger(__name__)


class EventState(Enum):
    """ State an event is in

    States:
    - ok - proceed
    - cancel - event is cancelled
    - terminate_soon - send a QUIT to the IRC server
    - terminate_now - abort library
    """

    ok = 0
    cancel = 1
    terminate_soon = 2
    terminate_now = 3


class Event:
    """ Basic event passing through """

    def __init__(self, event):
        self.event = event
        self.status = EventState.ok


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
    """ Manages event registration and calling """

    def __init__(self):
        # Contains event classes
        self.events_reg = dict() 

    def register_class(self, cls, type):
        """ Register a given event """

        if cls in self.events_reg:
            return

        logger.debug("Registering class %s with type %s", cls, type.__name__)

        # Set the events list
        self.events_reg[cls] = EventRegistry(dict(), type)

    def unregister_class(self, cls):
        """ Unregister a given event type """

        assert cls in self.events_reg

        logger.debug("Unregistering class %s", cls)

        del self.events_reg[cls]

    def clear(self):
        """ Clear all classes """

        logger.debug("Clearing hooks")
        self.events_reg.clear()

    def register_event(self, cls, event):
        """ Register a given event """

        assert cls in self.events_reg

        events = self.events_reg[cls][0]

        if event in events:
            return

        logger.debug("Creating event (class %s): %s", cls, event)
        events[event] = SimpleNamespace()
        events[event].items = []
        events[event].cur_id = 0

    def unregister_event(self, cls, event):
        """ Unregister a given event """

        assert cls in self.events_reg

        events = self.events_reg[cls][0]

        if event not in events:
            return

        logger.debug("Unregistering event (class %s): %s", cls, event)
        del events[event]

    def register_callback(self, cls, event, priority, callback):
        """ Register a callback for the given event """

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
        """ Unregister the given callback for an event """

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
        """ Call the callbacks for a given event """

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
                # TODO this will go away and events will handle this themselves
                # there may be a "hard" cancel in the future
                # For now this is just a compat shim
                break
            elif ev_inst.status == EventState.terminate_now:
                quit()

        return ev_inst
