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

from taillight.signal import Signal, SignalStop

from PyIRC.extension import BaseExtension
from PyIRC.numerics import Numerics


_logger = getLogger(__name__)


class CapNegotiate(BaseExtension):

    """Basic CAP negotiation.

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

    requires = ["BasicRFC"]

    """ Presently supported maximum CAP version. """
    version = "302"

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

    @staticmethod
    def extract_caps(line):
        """Extract caps from a line."""

        caps = line.params[-1].split()
        caps = (CapNegotiate.parse_cap(cap) for cap in caps)
        return {cap : param for cap, param in caps}

    @staticmethod
    def parse_cap(string):
        """Parse a capability string."""

        cap, sep, param = string.partition('=')
        if not sep:
            return (cap, [])

        return (cap, param.split(','))

    @staticmethod
    def create_str(cap, params):
        """Create a capability string."""

        if params:
            return "{}={}".format(cap, ','.join(params))
        else:
            return cap

    @Signal(("hooks", "connected")).add_wraps(priority=-1000))
    def send_cap(self, caller):
        if not self.negotiating:
            return

        _logger.debug("Requesting CAP list")

        self.send("CAP", ["LS", self.version])

        self.timer = self.schedule(15, partial(self.end, event))

        self.negotiating = True

        # Ensure no other connected events get fired
        raise SignalStop

    @Signal(("hooks", "disconnected")).add_wraps(priority=-1000))
    def close(self, caller):
        if self.timer is not None:
            try:
                self.unschedule(self.timer)
            except ValueError:
                pass

        self.supported.clear()
        self.remote.clear()
        self.local.clear()

    @Signal(("commands", "CAP")).add_wraps(priority=-1000))
    def dispatch(self, caller, line):
        """Dispatch the CAP command."""

        if self.timer is not None:
            try:
                self.unschedule(self.timer)
            except ValueError:
                pass
            self.timer = None

        cap_command = line.params[1].lower()
        self.call_event("commands_cap", cap_command, line)

    @Signal(("commands_cap", "new")).add_wraps(priority=-1000))
    @Signal(("commands_cap", "ls")).add_wraps(priority=-1000))
    def get_remote(self, caller, line):
        remote = self.extract_caps(line)
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
                _logger.debug("Requesting caps: %s", caps)
                self.send("CAP", ["REQ", caps])
            else:
                # Negotiaton ends, no caps
                _logger.debug("No CAPs to request!")
                self.end(event)

    @Signal(("commands_cap", "list")).add_wraps(priority=-1000))
    def get_local(self, caller, line):
        self.local = caps = self.extract_caps(line)
        _logger.debug("CAPs active: %s", caps)

    @Signal(("commands_cap", "ack")).add_wraps(priority=-1000))
    def ack(self, caller, line):
        caps = dict()
        for cap, params in self.extract_caps(line).items():
            if cap.startswith('-'):
                cap = cap[1:]
                _logger.debug("CAP removed: %s", cap)
                self.local.pop(cap, None)
                caps.pop(cap, None)  # Just in case
                continue
            elif cap.startswith(('=', '~')):
                # Compatibility stuff
                cap = cap[1:]

            assert cap in self.supported
            _logger.debug("Acknowledged CAP: %s", cap)
            caps[cap] = self.local[cap] = params

        self.call_event("cap_perform", "ack", line, caps)

    @Signal(("commands_cap", "nak")).add_wraps(priority=-1000))
    def nak(self, caller, line):
        _logger.warn("Rejected CAPs: %s", line.params[-1].lower())

    @Signal(("commands_cap", "end")).add_wraps(priority=-1000))
    @Signal(("commands", Numerics.RPL_HELLO)).add_wraps(priority=-1000))
    def end(self, caller, line):
        _logger.debug("Ending CAP negotiation")

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
        """Register that we support a specific CAP.

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
