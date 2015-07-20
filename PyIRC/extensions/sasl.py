#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Identification to services.

SASL is a mechanism used by IRCv3 to authenticate clients to services in a
standard and user-friendly way. A variety of mechanisms are supported by most
servers, but only PLAIN is supported by this module at the moment.

"""


from logging import getLogger
from base64 import b64encode

from taillight.signal import SignalStop, SignalDefer

from PyIRC.signal import event
from PyIRC.extensions import BaseExtension
from PyIRC.numerics import Numerics


_logger = getLogger(__name__)


class SASLBase(BaseExtension):

    """Base SASL support. Does nothing on its own.

    :ivar mechanisms:
        Mechanisms supported by the server

    :ivar authenticated:
        Whether or not we are authenticated to services

    """

    requires = ["CapNegotiate"]

    method = None
    """ Authentication method to use """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mechanisms = set()
        self.username = kwargs.get("sasl_username")
        self.password = kwargs.get("sasl_password")

        self.authenticated = False

    @property
    def caps(self):
        cap_negotiate = self.base.cap_negotiate

        if "sasl" not in cap_negotiate.remote:
            # No SASL
            return None
        elif not cap_negotiate.remote["sasl"]:
            # 3.1 style SASL
            _logger.debug("Registering old-style SASL capability")
            return {"sasl" : []}
        else:
            # 3.2 style SASL
            _logger.debug("Registering new-style SASL capability")
            return {"sasl" : [m.method for m in SASLBase.__subclasses__()]}

    @event("link", "disconnected")
    def close(self, _):
        self.mechanisms.clear()

    @event("cap_perform", "ack", priority=100)
    def auth(self, _, line, caps):
        # Lower priority to ensure STARTTLS comes before
        if "sasl" not in caps:
            return
        elif self.method is None:
            raise NotImplementedError("Need an authentication method!")

        self.authenticated = False

        cap_negotiate = self.base.cap_negotiate
        if cap_negotiate.remote["sasl"]:
            # 3.2 style
            params = cap_negotiate.remote["sasl"]
            self.mechanisms = set(c.lower() for c in params)

        self.send("AUTHENTICATE", [self.method])

        # Defer end of CAP
        raise SignalDefer()

    @event("commands", Numerics.RPL_SASLSUCCESS)
    def success(self, _, line):
        _logger.info("SASL authentication succeeded as %s", self.username)

        self.authenticated = True

        services_login = self.base.services_login
        if services_login:
            # No need to authenticate
            services_login.authenticated = True

        cap_negotiate = self.base.cap_negotiate
        self.resume_event("cap_perform", "ack")

    @event("commands", Numerics.ERR_SASLFAIL)
    @event("commands", Numerics.ERR_SASLTOOLONG)
    @event("commands", Numerics.ERR_SASLABORTED)
    def fail(self, _, line):
        _logger.info("SASL authentication failed as %s", self.username)

        cap_negotiate = self.base.cap_negotiate
        self.resume_event("cap_perform", "ack")

    @event("commands", Numerics.ERR_SASLALREADY)
    def already(self, _, line):
        _logger.critical("Tried to log in twice, this shouldn't happen!")

    @event("commands", Numerics.RPL_SASLMECHS)
    def get_mechanisms(self, _, line):
        self.mechanisms = set(line.params[1].lower().split(','))
        _logger.info("Supported SASL mechanisms: %r", self.mechanisms)


class SASLPlain(SASLBase):

    """PLAIN authentication.

    No security or encryption is performed on the string sent to the
    server, but still suitable for use over TLS.

    """

    method = "PLAIN"

    @event("commands", "AUTHENTICATE", priority=250)
    def authenticate(self, _, line):
        """Implement the plaintext authentication method."""
        # Priority is arbitrary atm, but should be the least preferred auth
        # method if more are implemented
        _logger.info("Logging in with PLAIN method as %s", self.username)

        if line.params[-1] != '+':
            return

        # Generate the string for sending
        sendstr = "{0}\0{0}\0{1}".format(self.username, self.password)
        sendstr = b64encode(sendstr.encode("utf-8", "replace"))

        # b64encode returns bytes, but our parser expects a str *sigh*
        sendstr = sendstr.decode("utf-8")

        # Split into 400-sized chunks
        for l in (sendstr[i:i + 400] for i in range(0, len(sendstr), 400)):
            self.send("AUTHENTICATE", [l])

        # Stop other auth methods.
        raise SignalStop
