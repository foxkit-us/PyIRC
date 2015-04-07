#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


from functools import partial
from logging import getLogger

from PyIRC.base import BaseExtension, PRIORITY_FIRST
from PyIRC.event import EventState, HookEvent, LineEvent
from PyIRC.numerics import Numerics


logger = getLogger(__name__)


class CapNegotiate(BaseExtension):

    """ Basic CAP negotiation

    IRCv3.2 negotiation is attempted, but earlier specifications will be used
    in a backwards compatible manner.
    """

    priority = PRIORITY_FIRST
    requires = ["BasicRFC"]

    version = "302"

    def __init__(self, base, **kwargs):

        self.base = base

        self.commands = {
            "CAP" : self.dispatch,
        }

        self.hooks = {
            "connected" : self.send_cap,
            "extension_post" : self.register_cap_hooks,
        }

        self.commands_cap = {
            "ls" : self.get_remote,
            "list" : self.get_local,
            "ack" : self.ack,
            "new" : self.get_remote,
            "nak" : self.nak,
            "end" : self.end,
        }

        # What we support - other extensions can add doodads to this
        self.supported = dict()

        # What they support
        self.remote = dict()

        # What we are actually using
        self.local = dict()

        # Negotiation phase
        self.negotiating = True

        # Timer for CAP disarm
        self.timer = None

    @staticmethod
    def extract_caps(line):
        """ Extract caps from a line """

        caps = line.params[-1].split()
        caps = (CapNegotiate.parse_cap(cap) for cap in caps)
        return {cap : param for cap, param in caps}

    @staticmethod
    def parse_cap(string):
        """ Parse a capability string """

        cap, sep, param = string.partition('=')
        if not sep:
            return (cap, [])

        return (cap, param.split(','))

    @staticmethod
    def create_str(cap, params):
        """ Create a capability string """

        if params:
            return "{}={}".format(cap, ','.join(params))
        else:
            return cap

    def register_cap_hooks(self, event):
        """ Register CAP hooks """

        self.base.events.register_class("commands_cap", LineEvent)
        self.base.build_hooks("commands_cap", "commands_cap", str.lower)

    def send_cap(self, event):
        """ Request capabilities from the server """

        if not self.negotiating:
            return

        logger.debug("Requesting CAP list")

        self.send("CAP", ["LS", self.version])

        self.timer = self.schedule(15, partial(self.end, event))

        self.negotiating = True

        # Ensure no others get fired
        event.status = EventState.cancel

    def close(self, event):
        """ Reset state on disconnect """

        if self.timer is not None:
            try:
                self.unschedule(self.timer)
            except ValueError:
                pass

        self.supported.clear()
        self.remote.clear()
        self.local.clear()

    def dispatch(self, event):
        """ Dispatch the CAP command """

        if self.timer is not None:
            try:
                self.unschedule(self.timer)
            except ValueError:
                pass
            self.timer = None

        cap_command = event.line.params[1].lower()
        self.base.call_event("commands_cap", cap_command, event.line)

    def get_remote(self, event):
        """ A list of the CAPs the server supports (CAP LS) """

        remote = self.extract_caps(event.line)
        self.remote.update(remote)

        for extension in self.base.extensions_db.values():
            # Scan the extensions for caps
            caps = getattr(extension, "caps", None)
            if not caps:
                # Unsupported
                continue

            for cap, param in caps.items():
                if cap.lower() not in remote:
                    continue

                self.register(cap, param)

        if self.negotiating:
            # Negotiate caps
            supported = self.supported
            supported = [self.create_str(c, v) for c, v in
                         remote.items() if c in supported]
            supported.sort()

            if supported:
                caps = ' '.join(supported)
                logger.debug("Requesting caps: %s", caps)
                self.send("CAP", ["REQ", caps])
            else:
                # Negotiaton ends, no caps
                logger.debug("No CAPs to request!")
                self.end(event)

    def get_local(self, event):
        """ caps presently in use """

        self.local = caps = extract_caps(event.line)
        logger.debug("CAPs active: %s", caps)

    def ack(self, event):
        """ Acknowledge a CAP ACK response """

        # XXX ghetto hack to avoid calling us again
        if not hasattr(event, "line"):
            return
        if event.line.command.lower() != "cap":
            return
        if event.line.params[1].lower() != "ack":
            return

        for cap, params in self.extract_caps(event.line).items():
            if cap.startswith('-'):
                cap = cap[1:]
                logger.debug("CAP removed: %s", cap)
                self.local.pop(cap, None)
                continue
            elif cap.startswith(('=', '~')):
                # Compatibility stuff
                cap = cap[1:]

            assert cap in self.supported
            logger.debug("Acknowledged CAP: %s", cap)
            self.local[cap] = params

    def nak(self, event):
        """ CAPs rejected """

        logger.warn("Rejected CAPs: %s", event.line.params[-1].lower())

    def cont(self, event):
        """ Continue negotiation of caps """

        status = self.call_event("commands_cap", "ack", event.line).status
        if status == EventState.ok:
            if self.negotiating:
                self.end(event)

    def end(self, event):
        """ End the CAP process """

        logger.debug("Ending CAP negotiation")

        if self.timer is not None:
            try:
                self.unschedule(self.timer)
            except ValueError:
                # Called from scheduler, ignore it
                pass
            self.timer = None

        self.send("CAP", ["END"])
        self.negotiating = False
        self.call_event("hooks", "connected")

    def register(self, cap, params=list(), replace=False):
        """ Register that we support a specific CAP """

        if replace or cap not in self.supported:
            self.supported[cap] = params
        else:
            self.supported[cap].extend(params)

    def deregister(self, cap):
        """ Unregister support for a specific CAP """

        self.supported.pop(cap, None)

