#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


from collections.abc import Mapping
from functools import partial
from logging import getLogger

from base import BaseExtension, PRIORITY_FIRST, EVENT_CONNECTED, EVENT_CANCEL
from numerics import Numerics


EVENT_CAP_LS = 3  # CAP ACK (pre) event
EVENT_CAP_ACK = 4  # CAP ACK (post) event


logger = getLogger(__name__)


class CapNegotiate(BaseExtension):

    """ Basic CAP negotiation (version 302) """

    priority = PRIORITY_FIRST
    requires = ["BasicRFC"]

    cap_version = "302"

    def __init__(self, base, **kwargs):

        self.base = base

        self.implements = {
            "CAP" : self.cap_dispatch,
        }

        self.hooks = {
            EVENT_CONNECTED : self.send_cap,
        }

        self.cap_dispatch_table = {
            "ls" : self.cap_get_remote,
            "list" : self.cap_get_local,
            "ack" : self.cap_ack,
            "nak" : self.cap_nak,
            "end" : self.cap_end,
        }

        # What we support - other extensions can add doodads to this
        self.cap_supported = dict()

        # What they support
        self.cap_remote = dict()

        # What we are actually using
        self.cap_local = dict()

        # Negotiation phase
        self.negotiating = True

        # Timer for CAP disarm
        self.cap_timer = None

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

    def create_cap_str(self, cap, params):
        """ Create a capability string """

        if params:
            return "{}={}".format(cap, ','.join(params))
        else:
            return cap

    def send_cap(self):
        """ Request capabilities from the server """

        logger.debug("Requesting CAP list")

        self.send("CAP", ["LS", self.cap_version])

        self.cap_timer = self.schedule(15, self.cap_end)

        # Ensure no others get fired
        return EVENT_CANCEL

    def cap_dispatch(self, line):
        """ Dispatch the CAP command """

        if self.cap_timer:
            # Rearm the timeout
            self.unschedule(self.cap_timer)
            self.cap_timer = self.schedule(15, self.cap_end)

        cap_cmd = line.params[1].lower()

        if cap_cmd not in self.cap_dispatch_table:
            # We shouldn't get here if servers obey the spec...
            logger.warn("Unhandled CAP command: %s", cap_cmd)
            return

        return self.cap_dispatch_table[cap_cmd](line)

    def cap_get_remote(self, line):
        """ A list of the CAPs the server supports (CAP LS) """

        self.cap_remote = cap_remote = self.extract_caps(line)

        if self.negotiating:
            # Allow extensions to register their own stuff
            if self.dispatch_event(self.base.hooks, EVENT_CAP_LS) is not None:
                return

            # Negotiate caps
            cap_supported = self.cap_supported
            supported = [self.create_cap_str(c, v) for c, v in
                         cap_remote.items() if c in cap_supported]

            if supported:
                caps = ' '.join(sorted(supported))
                logger.debug("Requesting caps: %s", caps)
                self.send("CAP", ["REQ", caps])
            else:
                # Negotiaton ends, no caps
                logger.debug("No CAPs to request!")
                self.cap_end()

    def cap_get_local(self, line):
        """ caps presently in use """

        self.cap_local = caps = extract_caps(line)
        logger.debug("CAPs active: %s", caps)

    def cap_ack(self, line):
        """ Acknowledge a CAP ACK response """

        for cap, params in self.extract_caps(line).items():
            if cap.startswith('-'):
                cap = cap[1:]
                logger.debug("CAP removed: %s", cap)
                self.cap_local.pop(cap, None)
                continue
            elif cap.startswith(('=', '~')):
                # Compatibility stuff
                cap = cap[1:]

            assert cap in self.cap_supported
            logger.debug("Acknowledged CAP: %s", cap)
            self.cap_local[cap] = params

        if self.dispatch_event(self.base.hooks, EVENT_CAP_ACK) is None:
            if self.negotiating:
                # Negotiation ends
                self.cap_end()

    def cap_nak(self, line):
        """ CAPs rejected """

        logger.warn("Rejected CAPs: %s", line.params[-1].lower())

    def cap_end(self, line=None):
        """ End the CAP process """

        logger.debug("Ending CAP negotiation")

        if self.cap_timer:
            try:
                self.unschedule(self.cap_timer)
            except ValueError:
                # Called from scheduler, ignore it
                pass
            self.cap_timer = None

        self.send("CAP", ["END"])
        self.get_extension("BasicRFC").handshake()
        self.negotiating = False
