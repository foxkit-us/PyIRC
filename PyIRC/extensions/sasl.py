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


_logger = getLogger(__name__)  # pylint: disable=invalid-name


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
        self.password = kwargs.get("sasl_password", None)

        self.authenticated = False

    @property
    def can_authenticate(self):
        """Whether or not we can authenticate with this method."""
        return False

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
            subclasses = SASLBase.__subclasses__()  # pylint: disable=no-member
            return {"sasl" : [m.method for m in subclasses]}

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

        if not self.can_authenticate:
            return

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

        self.resume_event("cap_perform", "ack")

    @event("commands", Numerics.ERR_SASLFAIL)
    @event("commands", Numerics.ERR_SASLTOOLONG)
    @event("commands", Numerics.ERR_SASLABORTED)
    def fail(self, _, line):
        _logger.info("SASL authentication failed as %s", self.username)

        self.resume_event("cap_perform", "ack")

    @event("commands", Numerics.ERR_SASLALREADY)
    def already(self, _, line):
        _logger.critical("Tried to log in twice, this shouldn't happen!")

    @event("commands", Numerics.RPL_SASLMECHS)
    def get_mechanisms(self, _, line):
        self.mechanisms = set(line.params[1].lower().split(','))
        _logger.info("Supported SASL mechanisms: %r", self.mechanisms)


class SASLExternal(SASLBase):

    """EXTERNAL authentication, usually CERTFP.

    .. warning::
        This is not recommended on servers that use SHA-1 as their certificate
        hashing mechanism (almost all), as SHA-1 is considered weak, and it is
        possible an adversary could collide your certificate in theory.

    """

    method = "EXTERNAL"

    @property
    def can_authenticate(self):
        """Whether or not we can authenticate with this method."""
        return self.ssl and self.password is None

    @event("commands", "AUTHENTICATE", priority=300)
    def authenticate(self, _, line):
        """Implement the EXTERNAL (certfp) authentication method."""
        # This is the least preferred auth method of them all, but will be
        # used if SSL is enabled and there is no password.
        _logger.info("Logging in with EXTERNAL method as %s", self.username)

        if line.params[-1] != '+':
            return

        # Generate the string for sending
        sendstr = "{0}\0{0}\0".format(self.username)
        sendstr = b64encode(sendstr.encode("utf-8", "replace"))

        # b64encode returns bytes, but our parser expects a str *sigh*
        sendstr = sendstr.decode("utf-8")

        # This should never exceed 400 bytes, so this is fine.
        self.send("AUTHENTICATE", [sendstr])

        # Stop other auth methods.
        raise SignalStop


class SASLPlain(SASLBase):

    """PLAIN authentication.

    No security or encryption is performed on the string sent to the
    server, but still suitable for use over TLS.

    """

    method = "PLAIN"

    @property
    def can_authenticate(self):
        """Whether or not we can authenticate with this method."""
        return self.username and self.password

    @event("commands", "AUTHENTICATE", priority=250)
    def authenticate(self, _, line):
        """Implement the plaintext authentication method."""
        # Priority is arbitrary atm, but should be the second least preferred
        # auth method if more are implemented
        if self.password is None:
            # No password, try to fall back.
            return

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
