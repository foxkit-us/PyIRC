#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


""" IRC CAP negotation sub-protocol extensions

For more information, see:
http://ircv3.atheme.org/specification/capability-negotiation-3.1
"""


from functools import partial
from logging import getLogger

from PyIRC.extension import BaseExtension
from PyIRC.hook import hook, PRIORITY_FIRST
from PyIRC.event import EventState, LineEvent
from PyIRC.numerics import Numerics


logger = getLogger(__name__)


class CAPEvent(LineEvent):

    """A CAP ACK/NEW event"""

    def __init__(self, event, line, caps):
        super().__init__(event, line)
        self.caps = caps

    @staticmethod
    def key(k):
        return k.lower()


class CapNegotiate(BaseExtension):

    """ Basic CAP negotiation

    IRCv3.2 negotiation is attempted, but earlier specifications will be used
    in a backwards compatible manner.

    This extension does little on its own, but provides a public API.

    This extension adds ``base.cap_negotiate`` as itself as an alias for
    ``get_extension("CapNegotiate").``.

    :ivar supported:
        Supported capabilities - these are the capabilities we support,
        at least, in theory.

    :ivar remote:
        Remote capabilities - that is, what the server supports.

    :ivar local:
        Local capabilities - these are what we actually support.

    :ivar negotiating:
        Whether or not CAP negotiation is in progress.
    """

    priority = PRIORITY_FIRST
    requires = ["BasicRFC"]

    """ Presently supported maximum CAP version. """
    version = "302"

    hook_classes = {
        "commands_cap": LineEvent,
        "cap_perform": CAPEvent,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base.cap_negotiate = self

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

        # pending ACK's to finish
        self.ack_chains = set()

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

    @hook("hooks", "connected")
    def send_cap(self, event):
        if not self.negotiating:
            return

        logger.debug("Requesting CAP list")

        self.send("CAP", ["LS", self.version])

        self.timer = self.schedule(15, partial(self.end, event))

        self.negotiating = True

        # Ensure no other connected events get fired
        event.status = EventState.cancel

    @hook("hooks", "disconnected")
    def close(self, event):
        if self.timer is not None:
            try:
                self.unschedule(self.timer)
            except ValueError:
                pass

        self.supported.clear()
        self.remote.clear()
        self.local.clear()

    @hook("commands", "CAP")
    def dispatch(self, event):
        """ Dispatch the CAP command """

        if self.timer is not None:
            try:
                self.unschedule(self.timer)
            except ValueError:
                pass
            self.timer = None

        cap_command = event.line.params[1].lower()
        self.call_event("commands_cap", cap_command, event.line)

    @hook("commands_cap", "new")
    @hook("commands_cap", "ls")
    def get_remote(self, event):
        remote = self.extract_caps(event.line)
        self.remote.update(remote)

        extensions = self.extensions
        for extension in extensions.db.values():
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
            supported = sorted([self.create_str(c, v) for c, v in
                                remote.items() if c in supported])

            if supported:
                caps = ' '.join(supported)
                logger.debug("Requesting caps: %s", caps)
                self.send("CAP", ["REQ", caps])
            else:
                # Negotiaton ends, no caps
                logger.debug("No CAPs to request!")
                self.end(event)

    @hook("commands_cap", "list")
    def get_local(self, event):
        self.local = caps = extract_caps(event.line)
        logger.debug("CAPs active: %s", caps)

    @hook("commands_cap", "ack")
    def ack(self, event):
        caps = dict()
        for cap, params in self.extract_caps(event.line).items():
            if cap.startswith('-'):
                cap = cap[1:]
                logger.debug("CAP removed: %s", cap)
                self.local.pop(cap, None)
                caps.pop(cap, None)  # Just in case
                continue
            elif cap.startswith(('=', '~')):
                # Compatibility stuff
                cap = cap[1:]

            assert cap in self.supported
            logger.debug("Acknowledged CAP: %s", cap)
            caps[cap] = self.local[cap] = params

        event = self.call_event("cap_perform", "ack", event.line, caps)
        if event.status != EventState.ok:
            self.ack_chains.add(event)

    @hook("commands_cap", "nak")
    def nak(self, event):
        logger.warn("Rejected CAPs: %s", event.line.params[-1].lower())

    @hook("commands_cap", "end")
    @hook("commands", Numerics.RPL_HELLO)
    def end(self, event):
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

        # Call the hooks to resume connection
        self.call_event("hooks", "connected")

    def register(self, cap, params=list(), replace=False):
        """Register that we support a specific CAP

        :param cap:
            The capability to register support for

        :param params:
            The parameters to pass for the CAP (IRCv3 extension)

        :param replace:
            Replace existing CAP report, if present
        """
        if replace or cap not in self.supported:
            self.supported[cap] = params
        else:
            self.supported[cap].extend(params)

    def unregister(self, cap):
        """Unregister support for a specific CAP.

        :param cap:
            Capability to remove
        """
        self.supported.pop(cap, None)

    def cont(self, event):
        """Continue negotiation of caps"""
        # Reset event status
        event.status = EventState.ok
        self.call_event_inst("cap_perform", "ack", event)
        if event.status == EventState.ok:
            self.ack_chains.discard(event)
            if not self.ack_chains and self.negotiating:
                # No more chains.
                self.end(event)
