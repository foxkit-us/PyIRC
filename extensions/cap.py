#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


from collections.abc import Mapping
from functools import partial
from logging import getLogger

from base import (BaseExtension, PRIORITY_FIRST, EVENT_CONNECTED,
                  EVENT_CANCEL, event_new)
from numerics import Numerics


EVENT_CAP_LS = event_new()  # CAP ACK (pre) event
EVENT_CAP_ACK = event_new()  # CAP ACK (post) event


logger = getLogger(__name__)


class CapNegotiate(BaseExtension):

    """ Basic CAP negotiation (version 302) """

    priority = PRIORITY_FIRST
    requires = ["BasicRFC"]

    version = "302"

    def __init__(self, base, **kwargs):

        self.base = base

        self.implements = {
            "CAP" : self.dispatch,
        }

        self.hooks = {
            EVENT_CONNECTED : self.send_cap,
        }

        self.dispatch_table = {
            "ls" : self.get_remote,
            "list" : self.get_local,
            "ack" : self.ack,
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

    def extract_caps(self, line):
        """ Extract caps from a line """

        caps = (self.parse_cap(cap) for cap in line.params[-1].split())
        return {cap : param for cap, param in caps}

    def parse_cap(self, string):
        """ Parse a capability string """

        cap, sep, param = string.partition('=')
        if not sep:
            return (cap, [])

        return (cap, param.split(','))

    def create_str(self, cap, params):
        """ Create a capability string """

        if params:
            return "{}={}".format(cap, ','.join(params))
        else:
            return cap

    def send_cap(self):
        """ Request capabilities from the server """

        logger.debug("Requesting CAP list")

        self.send("CAP", ["LS", self.version])

        self.timer = self.schedule(15, self.end)

        # Ensure no others get fired
        return EVENT_CANCEL

    def dispatch(self, line):
        """ Dispatch the CAP command """

        if self.timer is not None:
            try:
                self.unschedule(self.timer)
            except ValueError:
                pass
            self.timer = None

        cmd = line.params[1].lower()

        if cmd not in self.dispatch_table:
            # We shouldn't get here if servers obey the spec...
            logger.warn("Unhandled CAP command: %s", cmd)
            return

        return self.dispatch_table[cmd](line)

    def get_remote(self, line):
        """ A list of the CAPs the server supports (CAP LS) """

        self.remote = remote = self.extract_caps(line)

        if self.negotiating:
            # Allow extensions to register their own stuff
            if self.dispatch_event(self.base.hooks, EVENT_CAP_LS) is not None:
                return

            # Negotiate caps
            supported = self.supported
            supported = [self.create_str(c, v) for c, v in
                         remote.items() if c in supported]

            if supported:
                caps = ' '.join(sorted(supported))
                logger.debug("Requesting caps: %s", caps)
                self.send("CAP", ["REQ", caps])
            else:
                # Negotiaton ends, no caps
                logger.debug("No CAPs to request!")
                self.end()

    def get_local(self, line):
        """ caps presently in use """

        self.local = caps = extract_caps(line)
        logger.debug("CAPs active: %s", caps)

    def ack(self, line):
        """ Acknowledge a CAP ACK response """

        for cap, params in self.extract_caps(line).items():
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

        self.cont()

    def nak(self, line):
        """ CAPs rejected """

        logger.warn("Rejected CAPs: %s", line.params[-1].lower())

    def cont(self):
        """ Continue negotiation of caps """

        if self.dispatch_event(self.base.hooks, EVENT_CAP_ACK) is None:
            if self.negotiating:
                self.end()

    def end(self, line=None):
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
        self.get_extension("BasicRFC").handshake()
        self.negotiating = False

    def register(self, cap, params=list(), replace=False):
        """ Register that we support a specific CAP """

        if replace or cap not in self.supported:
            self.supported[cap] = params
        else:
            self.supported[cap].extend(params)

    def deregister(self, cap):
        """ Unregister support for a specific CAP """

        self.supported.pop(cap, None)

